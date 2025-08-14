from fastapi import APIRouter, Depends

from ..controllers import UserController

router = APIRouter()


@router.get("/users")
async def get_users(c: UserController = Depends(UserController)):
    return await c.get_collection()


@router.post("/users")
async def create_user(c: UserController = Depends(UserController)):
    return await c.create_user()
