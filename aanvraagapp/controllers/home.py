from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .. import models
from ..database import get_async_session
from ..dependencies import ValidateSession, ValidateSessionRes
from ..templates import templates


class HomeController:
    def __init__(
        self,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
        user=ValidateSession,
    ):
        self.request = request
        self.session = session
        self.user = user

    async def get_home(self):
        if not isinstance(self.user, models.User):
            return RedirectResponse(url="/login", status_code=302)

        # Fetch statistics using awaitable attributes
        listings_count = len(await self.user.awaitable_attrs.listings)
        applications_count = len(await self.user.awaitable_attrs.clients)
        
        # Count providers through listings
        providers_query = select(func.count(models.Provider.id)).select_from(
            models.Provider
        ).join(
            models.Listing, models.Listing.provider_id == models.Provider.id
        ).join(
            models.user_listing_association, models.user_listing_association.c.listing_id == models.Listing.id
        ).where(
            models.user_listing_association.c.user_id == self.user.id
        )
        providers_result = await self.session.execute(providers_query)
        providers_count = providers_result.scalar() or 0

        # Format creation date
        created_date = self.user.created_at.strftime("%B %d, %Y")

        return templates.TemplateResponse(
            "pages/home.jinja",
            {
                "request": self.request,
                "current_user": self.user,
                "greeting": f"Welcome back {self.user.first_name}!",
                "active_page": "home",
                "user_info": {
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                    "email": self.user.email,
                    "created_date": created_date,
                },
                "statistics": {
                    "listings": listings_count,
                    "applications": applications_count,
                    "providers": providers_count,
                }
            },
        )
