from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import EmailStr
from ..controllers import ValidateLogin, LoginAttemptRes
from ..database import DBSession
from ..models import User

router = APIRouter()
templates = Jinja2Templates(directory="aanvraagapp/templates")


class DummyUser:
    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    dummy_user = DummyUser("John", "Doe")
    return templates.TemplateResponse("pages/login.jinja", {"request": request, "active_page": "login"})


@router.post("/login")
async def login(request: Request, validate_login_result = ValidateLogin):
    match validate_login_result:
        case User():
            return RedirectResponse(url="/home", status_code=302)
        case (LoginAttemptRes, str() as email, str() as password):
            return templates.TemplateResponse("pages/login.jinja", {"request": request, "error": "Login failed because of invalid credentials.", "email": email, "password": password, "active_page": "login"})

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("pages/register.jinja", {"request": request, "active_page": "register"})
