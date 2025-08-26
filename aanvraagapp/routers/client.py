from fastapi import APIRouter, Depends, Request

from ..controllers import get_clients, get_client_detail, get_new_client, post_new_client

router = APIRouter()


@router.get("/clients")
async def get_clients_page(clients_page=Depends(get_clients)):
    return clients_page


@router.get("/clients/new")
async def get_new_client_page(new_client_page=Depends(get_new_client)):
    return new_client_page


@router.post("/clients/new")
async def post_new_client(new_client_page=Depends(post_new_client)):
    return new_client_page


@router.get("/clients/{client_id}")
async def get_client_detail_page(detail_client_page=Depends(get_client_detail)):
    return detail_client_page