from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, Request

from ..database import get_async_session
from .. import models
from ..dependencies import ValidateSession, ValidateSessionRes


class UserController:
    def __init__(
        self,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
        validate_session_res = ValidateSession,
    ):
        self.request = request
        self.session = session
        self.session_error = validate_session_res if isinstance(validate_session_res, ValidateSessionRes) else None
        self.user = validate_session_res if isinstance(validate_session_res, models.User) else None

    async def get_collection(self):
        """Get all users from the database"""
        result = await self.session.execute(select(models.User))
        users = result.scalars().all()
        return [{"id": user.id, "created_at": user.created_at, "updated_at": user.updated_at} for user in users]

    async def create_user(self):
        """Create a new user"""
        user = models.User()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return {"id": user.id, "created_at": user.created_at, "updated_at": user.updated_at}