from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from aanvraagapp.database import DBSession
from .. import models
from fastapi import Depends, Form

import secrets
from typing import Optional, Tuple, Union

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from enum import Enum


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
    email: EmailStr = Form(),
    password: str = Form(),
    session = DBSession,
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
        return LoginAttemptRes.EMAIL_404, email, password
    
    verified, updated_password_hash = password_helper.verify_and_update(
        password, user.hashed_password
    )

    if not verified:
        return LoginAttemptRes.WRONG_PASSWORD, email, password
    
    if updated_password_hash is not None:
        user.hashed_password = updated_password_hash
        session.add(user)
        await session.commit()
    
    return user


ValidateLogin: models.User | tuple[LoginAttemptRes, EmailStr, str] | tuple[LoginAttemptRes, EmailStr, str] = Depends(validate_login)