from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from ..database import get_async_session
from ..models import User


class UserController:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def get_collection(self):
        """Get all users from the database"""
        result = await self.session.execute(select(User))
        users = result.scalars().all()
        return [{"id": user.id, "created_at": user.created_at, "updated_at": user.updated_at} for user in users]

    async def create_user(self):
        """Create a new user"""
        user = User()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return {"id": user.id, "created_at": user.created_at, "updated_at": user.updated_at}