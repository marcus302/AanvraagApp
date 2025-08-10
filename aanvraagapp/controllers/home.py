from aanvraagapp.database import DBSession
from fastapi import Depends

async def get_home_data(
    session = DBSession,
):
    return "Hi Mark"


HomeData: str = Depends(get_home_data)