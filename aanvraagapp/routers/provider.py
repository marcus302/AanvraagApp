from fastapi import APIRouter, Depends, Request

from ..controllers import get_providers, get_provider_detail

router = APIRouter()


@router.get("/providers")
async def get_providers_page(providers_page=Depends(get_providers)):
    return providers_page


@router.get("/providers/{provider_id}")
async def get_provider_detail_page(detail_provider_page=Depends(get_provider_detail)):
    return detail_provider_page 