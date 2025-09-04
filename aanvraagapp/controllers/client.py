from fastapi import Form, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from pydantic import HttpUrl, ValidationError

from aanvraagapp.dependencies.auth import ValidateCSRFRes

from .. import models
from ..dependencies import ValidateCSRF, BasicDeps, RetrieveCSRF
from ..templates import templates
from ..parsing.website import extract_website_hierarchy
from ..parsing.utils import chunk_text, generate_embedding
from ..database import DBSessionContext


async def parse_website_background_task(client_id: int, website_url: str):
    """
    Background task to parse website hierarchy for a newly created client.
    This runs asynchronously after the client is created so the user gets immediate response.
    """
    try:
        # Extract website hierarchy using the parsing module
        all_urls, md_contents = await extract_website_hierarchy(website_url)

        assert len(all_urls) == len(md_contents)
        all_urls = [i for i, j in zip(all_urls, md_contents) if j is not None]
        md_contents = [j for i, j in zip(all_urls, md_contents) if j is not None]

        async with DBSessionContext() as session:
            result = await session.execute(
                select(models.Client)
                .where(
                    models.Client.id == client_id,
                )
            )
            client = result.scalar_one_or_none()

            if not client:
                raise ValueError("Cannot parse website for non existing client.")

            # Create a single ClientDocument with webpage type
            client_document = models.ClientDocument(
                doc_type=models.DocumentType.WEBPAGE,
                uri=website_url
            )
            session.add(client_document)
            await session.flush()  # Get the ID
            
            # Link the document to the client
            client.client_documents.append(client_document)
            
            # Process each md_content through chunking and embedding
            for i, md_content in enumerate(md_contents):
                # Split content into chunks
                chunks = chunk_text(md_content, chunk_size=1024, overlap=128)
                
                for j, chunk_content in enumerate(chunks):
                    try:
                        # Generate embedding for each chunk
                        embedding = await generate_embedding(chunk_content)
                        
                        # Create ClientDocumentChunk
                        chunk = models.ClientDocumentChunk(
                            document_id=client_document.id,
                            content=chunk_content,
                            emb=embedding
                        )
                        session.add(chunk)
                        
                    except Exception as e:
                        print(f"Error processing chunk {j+1} of content {i+1}: {e}")
                        continue
                
                print(f"Processed {len(chunks)} chunks for content {i+1}")
            
            await session.commit()
            print(f"Successfully saved website parsing results for client {client_id}")

    except Exception as e:
        # Log any errors that occur during parsing
        print(f"Error parsing website for client {client_id}: {e}")


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


async def post_new_client(background_tasks: BackgroundTasks, deps=BasicDeps, csrf=ValidateCSRF, name: str = Form(), website: str = Form()):
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

    # Validate name is not empty
    if not name or not name.strip():
        return templates.TemplateResponse(
            "pages/client/new-client.jinja",
            {
                "request": deps.request,
                "current_user": deps.user,
                "active_page": "clients",
                "csrf_token": csrf,
                "error": "Please enter a client name",
                "name": name,
                "website": website,
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
                "name": name,
                "website": website,
            },
        )

    new_client = models.Client(name=name.strip(), website=website)
    deps.session.add(new_client)
    await deps.session.flush()
    await deps.user.awaitable_attrs.clients
    deps.user.clients.append(new_client)
    await deps.session.commit()

    # Add background task to parse the website
    background_tasks.add_task(parse_website_background_task, new_client.id, website)

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
