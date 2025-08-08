from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

async def validate_login_attempt(
    username: EmailStr,
    password: str,
    session: AsyncSession,
):
    pass