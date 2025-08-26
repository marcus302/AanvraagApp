from fastapi import APIRouter, Depends, Request

from ..controllers import get_home

router = APIRouter()


@router.get("/home")
async def get_home_page(home_page=Depends(get_home)):
    return home_page
