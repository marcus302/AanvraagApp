from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from aanvraagapp.database import DBSession, RedisSession
from .. import models
from fastapi import Depends, Form, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

import secrets
import json
import hmac
import hashlib
from typing import Optional, Tuple, Union
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from enum import Enum

# Magic constants
SESSION_SECRET_KEY = "your-super-secret-key-change-in-production"  # TODO: Move to env vars
SESSION_EXPIRY_HOURS = 24  # TODO: Move to env vars
SESSION_COOKIE_NAME = "session_token"


class PasswordHelper:
    def __init__(self, password_hash: Optional[PasswordHash] = None) -> None:
        if password_hash is None:
            self.password_hash = PasswordHash(
                (
                    Argon2Hasher(),
                )
            )
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
        password_helper.hash(password)
        return LoginAttemptRes.EMAIL_404
    
    verified, updated_password_hash = password_helper.verify_and_update(
        password, user.hashed_password
    )

    if not verified:
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
    redis_client = RedisSession,
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
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRY_HOURS)).isoformat()
    }
    
    session_data_str = json.dumps(session_data, sort_keys=True)
    signature = hmac.new(
        SESSION_SECRET_KEY.encode(),
        session_data_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    redis_key = f"session:{session_token}"
    await redis_client.setex(
        redis_key,
        SESSION_EXPIRY_HOURS * 3600,  # Convert hours to seconds
        json.dumps({
            "data": session_data,
            "signature": signature
        })
    )
    
    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_EXPIRY_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="strict"
    )
    
    return response


class ValidateSessionRes(Enum):
    NO_TOKEN_GIVEN = "no_token_found"
    NO_TOKEN_FOUND = "no_token_found_in_redis"
    PARSING_ERROR = "parsing_error"
    WRONG_SIGNATURE = "wrong_signature"
    FOUND_TOKEN_EXPIRED = "found_token_expired"
    NO_USER_FOUND = "no_user_found"


async def validate_session(
    request: Request,
    session: AsyncSession = DBSession,
    redis_client = RedisSession,
):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)    
    if not session_token:
        return ValidateSessionRes.NO_TOKEN_GIVEN
    
    redis_key = f"session:{session_token}"
    session_data_json = await redis_client.get(redis_key)
    
    if not session_data_json:
        return ValidateSessionRes.NO_TOKEN_FOUND
    
    try:
        session_data = json.loads(session_data_json)
        stored_data = session_data["data"]
        stored_signature = session_data["signature"]
        
        data_str = json.dumps(stored_data, sort_keys=True)
        expected_signature = hmac.new(
            SESSION_SECRET_KEY.encode(),
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(stored_signature, expected_signature):
            await redis_client.delete(redis_key)
            return ValidateSessionRes.WRONG_SIGNATURE
        
        expires_at = datetime.fromisoformat(stored_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            await redis_client.delete(redis_key)
            return ValidateSessionRes.FOUND_TOKEN_EXPIRED
        
        result = await session.execute(
            select(models.User).where(models.User.id == stored_data["user_id"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await redis_client.delete(redis_key)
            return ValidateSessionRes.NO_USER_FOUND
        
        return user
        
    except (json.JSONDecodeError, KeyError, ValueError):
        await redis_client.delete(redis_key)
        return ValidateSessionRes.PARSING_ERROR


ValidateLogin: RedirectResponse | tuple[LoginAttemptRes, EmailStr, str] | tuple[LoginAttemptRes, EmailStr, str] = Depends(create_session_and_login)
ValidateSession: models.User | ValidateSessionRes = Depends(validate_session)