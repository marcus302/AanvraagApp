from fastapi import APIRouter, Depends
from ..controllers import UserController

router = APIRouter()


@router.get(
    "/users"
)
async def get_users(c: UserController = Depends(UserController)):
    return await c.get_collection()