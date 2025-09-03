from fastapi import Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from pydantic import HttpUrl, ValidationError

from aanvraagapp.dependencies.auth import ValidateCSRFRes

from .. import models
from ..dependencies import ValidateCSRF, BasicDeps, RetrieveCSRF
from ..templates import templates


async def get_providers(deps=BasicDeps):
    if not isinstance(deps.user, models.User):
        return RedirectResponse(url="/login", status_code=302)

    # Get all providers (no user association table exists, so all providers are accessible)
    result = await deps.session.execute(select(models.Provider))
    providers = result.scalars().all()

    return templates.TemplateResponse(
        "pages/provider/providers.jinja",
        {
            "request": deps.request,
            "current_user": deps.user,
            "active_page": "providers",
            "providers": providers,
        },
    )


async def get_provider_detail(provider_id: int, deps=BasicDeps):
    if not isinstance(deps.user, models.User):
        return RedirectResponse(url="/login", status_code=302)
    
    result = await deps.session.execute(
        select(models.Provider).where(models.Provider.id == provider_id)
    )
    provider = result.scalar_one_or_none()

    if not provider:
        return templates.TemplateResponse(
            "pages/404.jinja",
            {
                "request": deps.request,
                "current_user": deps.user,
                "active_page": "providers",
                "return_url_for": "get_providers_page",
                "return_url_for_params": {},
                "return_message": "Go back to providers.",
            },
        )

    return templates.TemplateResponse(
        "pages/provider/provider-detail.jinja",
        {
            "request": deps.request,
            "current_user": deps.user,
            "active_page": "providers",
            "provider": provider,
        },
    ) 