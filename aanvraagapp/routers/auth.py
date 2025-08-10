from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from ..database import DBSession, RedisSession
from ..models import User
from ..dependencies import ValidateLogin, LoginAttemptRes
from ..templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("pages/login.jinja", {"request": request, "active_page": "login"})


@router.post("/login")
async def login(
    request: Request, 
    validate_login_result = ValidateLogin
):
    match validate_login_result:
        case RedirectResponse():
            return validate_login_result
        case (LoginAttemptRes.EMAIL_404 | LoginAttemptRes.WRONG_PASSWORD, str() as email, str() as password):
            return templates.TemplateResponse(
                "pages/login.jinja", 
                {
                    "request": request, 
                    "error": "Login failed because of invalid credentials.", 
                    "email": email, 
                    "password": password, 
                    "active_page": "login"
                }
            )


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("pages/register.jinja", {"request": request, "active_page": "register"})


@router.get("/logout")
async def logout(
    request: Request,
    redis_client = RedisSession
):
    session_token = request.cookies.get("session_token")
    
    if session_token:
        redis_key = f"session:{session_token}"
        await redis_client.delete(redis_key)
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    
    return response
