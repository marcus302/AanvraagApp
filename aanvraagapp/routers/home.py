from fastapi import APIRouter, Depends, Request
from ..controllers import HomeData
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="aanvraagapp/templates")


class DummyUser:
    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name


@router.get("/home")
async def get_home_page(request: Request, home_data = HomeData):
    dummy_user = DummyUser("John", "Doe")
    return templates.TemplateResponse("pages/home.jinja", {"request": request, "current_user": dummy_user, "greeting": home_data})