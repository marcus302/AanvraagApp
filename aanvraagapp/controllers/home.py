from fastapi.responses import RedirectResponse
from sqlalchemy import select, func

from .. import models
from ..dependencies import BasicDeps
from ..templates import templates


async def get_home(deps=BasicDeps):
    if not isinstance(deps.user, models.User):
        return RedirectResponse(url="/login", status_code=302)

    # Fetch statistics using awaitable attributes
    listings_count = len(await deps.user.awaitable_attrs.listings)
    applications_count = len(await deps.user.awaitable_attrs.clients)
    
    # Count providers through listings
    providers_query = select(func.count(models.Provider.id)).select_from(
        models.Provider
    ).join(
        models.Listing, models.Listing.provider_id == models.Provider.id
    ).join(
        models.user_listing_association, models.user_listing_association.c.listing_id == models.Listing.id
    ).where(
        models.user_listing_association.c.user_id == deps.user.id
    )
    providers_result = await deps.session.execute(providers_query)
    providers_count = providers_result.scalar() or 0

    # Format creation date
    created_date = deps.user.created_at.strftime("%B %d, %Y")

    return templates.TemplateResponse(
        "pages/home.jinja",
        {
            "request": deps.request,
            "current_user": deps.user,
            "greeting": f"Welcome back {deps.user.first_name}!",
            "active_page": "home",
            "user_info": {
                "first_name": deps.user.first_name,
                "last_name": deps.user.last_name,
                "email": deps.user.email,
                "created_date": created_date,
            },
            "statistics": {
                "listings": listings_count,
                "applications": applications_count,
                "providers": providers_count,
            }
        },
    )
