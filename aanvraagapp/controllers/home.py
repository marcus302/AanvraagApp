from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse

from ..database import get_async_session
from .. import models
from ..dependencies import ValidateSession, ValidateSessionRes
from ..templates import templates


class HomeController:
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

    async def get_home(self):
        if self.session_error:
            return RedirectResponse(url="/login", status_code=302)
        
        return templates.TemplateResponse(
            "pages/home.jinja",
            {
                "request": self.request,
                "current_user": self.user,
                "greeting": f"Welcome back {self.user.first_name}!",
                "active_page": "home",
            }
        )
