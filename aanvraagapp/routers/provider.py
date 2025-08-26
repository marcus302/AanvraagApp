from fastapi import APIRouter, Depends, Request

from ..controllers import get_providers, get_provider_detail, get_new_provider, post_new_provider

router = APIRouter()


@router.get("/providers")
async def get_providers_page(providers_page=Depends(get_providers)):
    return providers_page


@router.get("/providers/new")
async def get_new_provider_page(new_provider_page=Depends(get_new_provider)):
    return new_provider_page


@router.post("/providers/new")
async def post_new_provider(new_provider_page=Depends(post_new_provider)):
    return new_provider_page


@router.get("/providers/{provider_id}")
async def get_provider_detail_page(detail_provider_page=Depends(get_provider_detail)):
    return detail_provider_page 