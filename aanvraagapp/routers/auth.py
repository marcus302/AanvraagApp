from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..database import RedisSession
from ..dependencies import LoginAttemptRes, RedirectIfAuthenticated, ValidateLogin
from ..templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request, redirect_result=RedirectIfAuthenticated):
    if redirect_result:
        return redirect_result
    return templates.TemplateResponse(
        "pages/login.jinja", {"request": request, "active_page": "login"}
    )


@router.post("/login")
async def post_login(request: Request, validate_login_result=ValidateLogin):
    match validate_login_result:
        case RedirectResponse():
            return validate_login_result
        case (
            LoginAttemptRes.EMAIL_404 | LoginAttemptRes.WRONG_PASSWORD,
            str() as email,
            str() as password,
        ):
            return templates.TemplateResponse(
                "pages/login.jinja",
                {
                    "request": request,
                    "error": "Login failed because of invalid credentials.",
                    "email": email,
                    "password": password,
                    "active_page": "login",
                },
            )


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request, redirect_result=RedirectIfAuthenticated):
    if redirect_result:
        return redirect_result
    return templates.TemplateResponse(
        "pages/register.jinja", {"request": request, "active_page": "register"}
    )


@router.get("/logout")
async def logout(request: Request, redis_client=RedisSession):
    session_token = request.cookies.get("session_token")

    if session_token:
        redis_key = f"session:{session_token}"
        await redis_client.delete(redis_key)

    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")

    return response
