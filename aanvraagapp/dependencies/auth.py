import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Tuple, Union, cast

from fastapi import Depends, Form, Request, Cookie
from fastapi.responses import RedirectResponse
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pydantic import EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Template

from aanvraagapp.database import DBSession, RedisSession
from aanvraagapp.templates import templates
from aanvraagapp.email import send_email_mailhog

from .. import models

# Set up logger
logger = logging.getLogger(__name__)

# Magic constants
SESSION_EXPIRY_HOURS = 24  # TODO: Move to env vars
SESSION_COOKIE_NAME = "session_token"


class PasswordHelper:
    def __init__(self, password_hash: Optional[PasswordHash] = None) -> None:
        if password_hash is None:
            self.password_hash = PasswordHash((Argon2Hasher(),))
        else:
            self.password_hash = password_hash  # pragma: no cover

    def verify_and_update(
        self, plain_password: str, hashed_password: str
    ) -> Tuple[bool, Union[str, None]]:
        return self.password_hash.verify_and_update(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def generate(self) -> str:
        return secrets.token_urlsafe()


password_helper = PasswordHelper()


class LoginAttemptRes(Enum):
    EMAIL_404 = "email_404"
    WRONG_PASSWORD = "wrong_password"


async def validate_login(
    email: EmailStr,
    password: str,
    session: AsyncSession,
):
    result = await session.execute(
        select(models.User).where(
            # TODO: func.strip does not exist...
            func.lower(models.User.email) == email.strip().lower(),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Prevent timing attacks
        password_helper.hash(password)
        logger.info(f"Login attempt failed: email not found for {email}")
        return LoginAttemptRes.EMAIL_404

    verified, updated_password_hash = password_helper.verify_and_update(
        password, user.hashed_password
    )

    if not verified:
        logger.info(f"Login attempt failed: wrong password for {email}")
        return LoginAttemptRes.WRONG_PASSWORD

    if updated_password_hash is not None:
        user.hashed_password = updated_password_hash
        session.add(user)
        await session.commit()

    return user


async def create_session_and_login(
    email: EmailStr = Form(),
    password: str = Form(),
    session: AsyncSession = DBSession,
    redis_client=RedisSession,
):
    login_result = await validate_login(email=email, password=password, session=session)
    if login_result in (LoginAttemptRes.EMAIL_404, LoginAttemptRes.WRONG_PASSWORD):
        return login_result, email, password

    session_token = secrets.token_urlsafe(32)
    session_data = {
        "user_id": login_result.id,
        "email": login_result.email,
        "first_name": login_result.first_name,
        "last_name": login_result.last_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (
            datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRY_HOURS)
        ).isoformat(),
        "csrf": secrets.token_urlsafe(32)
    }

    redis_key = f"session:{session_token}"
    await redis_client.setex(
        redis_key,
        SESSION_EXPIRY_HOURS * 3600,  # Convert hours to seconds
        json.dumps(session_data),
    )

    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_EXPIRY_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return response


ValidateLogin: (
    RedirectResponse
    | tuple[LoginAttemptRes, EmailStr, str]
) = Depends(create_session_and_login)


class GetSessionFromRedisRes(Enum):
    NO_TOKEN_GIVEN = "no_token_given"
    NO_TOKEN_FOUND = "no_token_found"


async def get_session_and_key_from_redis(request: Request, redis_client=RedisSession):
    # Were are getting the cookie from request manually this way,
    # so that FastAPI does not consider it to be an obligatory dependency
    # for all dependencies that (indirectly) use this, such as through
    # redirect_if_authenticated.
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        logger.info("Session validation failed: no token given")
        return GetSessionFromRedisRes.NO_TOKEN_GIVEN

    redis_key = f"session:{session_token}"
    session_data = json.loads(await redis_client.get(redis_key))

    if not session_data:
        logger.info("Session validation failed: no token found in Redis")
        return GetSessionFromRedisRes.NO_TOKEN_FOUND

    # TODO: Fix typing issues with this object more elegantly.   
    return cast(dict[str, str], session_data), redis_key


GetSessionFromRedis: tuple[dict[str, str], str] | GetSessionFromRedisRes = Depends(get_session_and_key_from_redis)


class ValidateSessionRes(Enum):
    NO_TOKEN_FOUND = "no_token_found"
    PARSING_ERROR = "parsing_error"
    FOUND_TOKEN_EXPIRED = "found_token_expired"
    NO_USER_FOUND = "no_user_found"


async def validate_session(
    session: AsyncSession = DBSession,
    session_and_key=GetSessionFromRedis,
    redis_client=RedisSession,
):
    if isinstance(session_and_key, GetSessionFromRedisRes):
        return ValidateSessionRes.NO_TOKEN_FOUND

    session_data, redis_key = session_and_key

    try:
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            await redis_client.delete(redis_key)
            logger.info("Session validation failed: token expired")
            return ValidateSessionRes.FOUND_TOKEN_EXPIRED

        result = await session.execute(
            select(models.User).where(models.User.id == session_data["user_id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            await redis_client.delete(redis_key)
            logger.warning(
                f"Session validation failed: no user found for user_id {session_data['user_id']}"
            )
            return ValidateSessionRes.NO_USER_FOUND

        # Refresh session expiry time
        await redis_client.expire(redis_key, SESSION_EXPIRY_HOURS * 3600)

        return user

    except (json.JSONDecodeError, KeyError, ValueError):
        await redis_client.delete(redis_key)
        logger.error("Session validation failed: parsing error", exzc_info=True)
        return ValidateSessionRes.PARSING_ERROR


ValidateSession: models.User | ValidateSessionRes = Depends(validate_session)


async def redirect_if_authenticated(
    validate_session_result=ValidateSession,
) -> RedirectResponse | None:
    """Redirect to /home if user has valid session, otherwise return None"""
    if isinstance(validate_session_result, models.User):
        return RedirectResponse(url="/home", status_code=302)
    return None


RedirectIfAuthenticated: RedirectResponse | None = Depends(redirect_if_authenticated)


class ValidateCSRFRes(Enum):
    NO_TOKEN_FOUND = "no_token_found"
    ERROR = "error"
    VALID = "valid"


async def validate_csrf(
    csrf: str = Form(),
    session_and_key=GetSessionFromRedis,
):
    if isinstance(session_and_key, GetSessionFromRedisRes):
        logger.info("CSRF validation failed: no session token found")
        return ValidateCSRFRes.NO_TOKEN_FOUND
    
    session_data, _ = session_and_key

    if secrets.compare_digest(csrf, session_data["csrf"]):
        logger.info("CSRF validation successful")
        return ValidateCSRFRes.VALID
    
    logger.warning("CSRF validation failed: token mismatch")
    return ValidateCSRFRes.ERROR


ValidateCSRF: ValidateCSRFRes = Depends(validate_csrf)


class RetrieveCSRFRes(Enum):
    NO_TOKEN_FOUND = "no_token_found"


async def get_csrf(
    session_and_key=GetSessionFromRedis,
):
    if isinstance(session_and_key, GetSessionFromRedisRes):
        logger.info("CSRF token retrieval failed: no session token found")
        return RetrieveCSRFRes.NO_TOKEN_FOUND
    
    session_data, _ = session_and_key
    return session_data["csrf"]


RetrieveCSRF: str | RetrieveCSRFRes = Depends(get_csrf)


class ForgotPasswordRes(Enum):
    EMAIL_404 = "email_404"
    FORGOT_PW_EMAIL_SENT = "forgot_pw_email_sent"


async def forgot_password(
    email: EmailStr = Form(),
    session: AsyncSession = DBSession,
    redis_client=RedisSession,
):
    result = await session.execute(
        select(models.User).where(
            # TODO: func.strip does not exist...
            func.lower(models.User.email) == email.strip().lower(),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        template = cast(
            Template, templates.get_template("email/forgot_password_404.jinja")
        )
        rendered_template = template.render()
        await send_email_mailhog(email, rendered_template, "Onbekend Account")
        logger.info(f"Password reset attempt failed: email not found for {email}")
        return ForgotPasswordRes.EMAIL_404

    forgot_pw_token = secrets.token_urlsafe(32)
    forgot_pw_url = f"https://localhost:80/reset-password?token={forgot_pw_token}"

    forgot_pw_data = {
        "user_id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
    }

    redis_key = f"password-forgot:{forgot_pw_token}"
    await redis_client.setex(redis_key, 15 * 60, json.dumps(forgot_pw_data))

    template = cast(Template, templates.get_template("email/forgot_password.jinja"))
    rendered_template = template.render(
        first_name=user.first_name,
        last_name=user.last_name,
        reset_password_url=forgot_pw_url,
        n_minutes_till_expiry=15,
    )
    await send_email_mailhog(user.email, rendered_template, "Nieuw Wachtwoord")
    logger.info(f"Password reset email sent for {user.email}")
    return ForgotPasswordRes.FORGOT_PW_EMAIL_SENT


ForgotPassword: ForgotPasswordRes = Depends(forgot_password)


class ResetPasswordRes(Enum):
    NO_TOKEN_FOUND = "no_token_found"
    PARSING_ERROR = "parsing_error"
    FOUND_TOKEN_EXPIRED = "found_token_expired"
    NO_USER_FOUND = "no_user_found"
    SUCCESS = "success"


async def reset_password(
    token: str = Form(),
    new_password: str = Form(),
    session: AsyncSession = DBSession,
    redis_client=RedisSession,
):
    redis_key = f"password-forgot:{token}"
    forgot_pw_data_json = await redis_client.get(redis_key)

    if not forgot_pw_data_json:
        logger.info(f"Password reset attempt failed: no token found for token {token}")
        return ResetPasswordRes.NO_TOKEN_FOUND

    try:
        forgot_pw_data = json.loads(forgot_pw_data_json)
        expires_at = datetime.fromisoformat(forgot_pw_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            await redis_client.delete(redis_key)
            logger.info(f"Password reset attempt failed: token expired for token {token}")
            return ResetPasswordRes.FOUND_TOKEN_EXPIRED
        result = await session.execute(
            select(models.User).where(models.User.id == forgot_pw_data["user_id"])
        )
        user = result.scalar_one_or_none()
        if not user:
            await redis_client.delete(redis_key)
            logger.error(
                f"Password reset attempt failed: no user found for user_id {forgot_pw_data['user_id']}"
            )
            return ResetPasswordRes.NO_USER_FOUND
    except (json.JSONDecodeError, KeyError, ValueError):
        await redis_client.delete(redis_key)
        logger.error("Password reset attempt failed: parsing error", exc_info=True)
        return ResetPasswordRes.PARSING_ERROR

    user.hashed_password = password_helper.hash(new_password)
    session.add(user)
    await session.commit()
    logger.info(f"Password reset successful for user {user.email}")
    return ResetPasswordRes.SUCCESS


ResetPassword: ResetPasswordRes = Depends(reset_password)