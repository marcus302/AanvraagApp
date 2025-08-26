from fastapi import Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from pydantic import HttpUrl, ValidationError

from aanvraagapp.dependencies.auth import ValidateCSRFRes

from .. import models
from ..dependencies import ValidateCSRF, BasicDeps, RetrieveCSRF
from ..templates import templates


async def get_clients(deps=BasicDeps):
    if not isinstance(deps.user, models.User):
        return RedirectResponse(url="/login", status_code=302)

    clients = await deps.user.awaitable_attrs.clients

    return templates.TemplateResponse(
        "pages/client/clients.jinja",
        {
            "request": deps.request,
            "current_user": deps.user,
            "active_page": "clients",
            "clients": clients,
        },
    )


async def get_new_client(deps=BasicDeps, csrf=RetrieveCSRF):
    if not isinstance(deps.user, models.User) or not isinstance(csrf, str):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "pages/client/new-client.jinja",
        {
            "request": deps.request,
            "current_user": deps.user,
            "active_page": "clients",
            "csrf_token": csrf,
        },
    )


async def post_new_client(deps=BasicDeps, csrf=ValidateCSRF, website: str = Form()):
    if not isinstance(deps.user, models.User):
        return RedirectResponse(url="/login", status_code=302)
    
    if csrf != ValidateCSRFRes.VALID:
        return templates.TemplateResponse(
            "pages/403.jinja",
            {
                "request": deps.request,
                "current_user": deps.user,
                "active_page": "clients",
            },
        )

    try:
        HttpUrl(website)
    except ValidationError:
        return templates.TemplateResponse(
            "pages/client/new-client.jinja",
            {
                "request": deps.request,
                "current_user": deps.user,
                "active_page": "clients",
                "csrf_token": csrf,
                "error": "Please enter a valid website URL",
                "website": website,
            },
        )

    new_client = models.Client(website=website)
    deps.session.add(new_client)
    await deps.session.flush()
    await deps.user.awaitable_attrs.clients
    deps.user.clients.append(new_client)
    await deps.session.commit()

    return RedirectResponse(url="/clients", status_code=302)


async def get_client_detail(client_id: int, deps=BasicDeps):
    if not isinstance(deps.user, models.User):
        return RedirectResponse(url="/login", status_code=302)
    
    result = await deps.session.execute(
        select(models.Client)
        .join(models.user_client_association)
        .where(
            models.Client.id == client_id,
            models.user_client_association.c.user_id == deps.user.id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        result = await deps.session.execute(
            select(models.Client).where(models.Client.id == client_id)
        )
        client_exists = result.scalar_one_or_none()
        
        if not client_exists:
            # Client doesn't exist at all - return 404
            return templates.TemplateResponse(
                "pages/404.jinja",
                {
                    "request": deps.request,
                    "current_user": deps.user,
                    "active_page": "clients",
                    "return_url_for": "get_clients_page",
                    "return_url_for_params": {},
                    "return_message": "Go back to clients.",
                },
            )
        else:
            # Client exists but user doesn't have access - return 403
            return templates.TemplateResponse(
                "pages/403.jinja",
                {
                    "request": deps.request,
                    "current_user": deps.user,
                    "active_page": "clients",
                    "return_url_for": "get_clients_page",
                    "return_url_for_params": {},
                    "return_message": "Go back to clients.",
                },
            )

    return templates.TemplateResponse(
        "/pages/client/client-detail.jinja",
        {
            "request": deps.request,
            "current_user": deps.user,
            "active_page": "clients",
            "client": client,
        },
    )
