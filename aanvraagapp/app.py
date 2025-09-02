import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from aanvraagapp.routers import auth_router, home_router, client_router, provider_router
from aanvraagapp.config import settings


# Configure logging to output to stdout/stderr for Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# app.mount("/static", StaticFiles(directory="aanvraagapp/static"), name="static")

app.include_router(auth_router)
app.include_router(home_router)
app.include_router(client_router)
app.include_router(provider_router)
