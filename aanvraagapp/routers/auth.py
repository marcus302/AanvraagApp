from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

router = APIRouter()
templates = Jinja2Templates(directory="aanvraagapp/templates")


class DummyUser:
    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    dummy_user = DummyUser("John", "Doe")
    return templates.TemplateResponse("pages/login.jinja", {"request": request, "current_user": dummy_user, "active_page": "login"})


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("pages/register.jinja", {"request": request, "active_page": "register"})
