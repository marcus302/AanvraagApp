from aanvraagapp.dependencies.auth import ValidateSession, ValidateSessionRes
from aanvraagapp.database import DBSession
from aanvraagapp import models
from dataclasses import dataclass

from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class GenDeps:
    request: Request
    session: AsyncSession
    user: ValidateSessionRes | models.User


async def get_deps(request: Request, session=DBSession, user=ValidateSession):
    return GenDeps(request, session, user)


BasicDeps: GenDeps = Depends(get_deps)