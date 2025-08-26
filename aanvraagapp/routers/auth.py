from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from ..database import RedisSession
from ..dependencies import (
    LoginAttemptRes,
    RedirectIfAuthenticated,
    ValidateLogin,
    ForgotPassword,
    ResetPassword,
    ResetPasswordRes,
)
from ..templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request, redirect_result=RedirectIfAuthenticated):
    if redirect_result:
        return redirect_result
    return templates.TemplateResponse(
        "pages/login.jinja", {"request": request, "active_page": "login"}
    )


@router.post("/login", response_class=HTMLResponse)
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


# @router.get("/register", response_class=HTMLResponse)
# async def register(request: Request, redirect_result=RedirectIfAuthenticated):
#     if redirect_result:
#         return redirect_result
#     return templates.TemplateResponse(
#         "pages/register.jinja", {"request": request, "active_page": "register"}
#     )


@router.get("/logout")
async def get_logout(request: Request, redis_client=RedisSession):
    session_token = request.cookies.get("session_token")

    if session_token:
        redis_key = f"session:{session_token}"
        await redis_client.delete(redis_key)

    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")

    return response


@router.get("/forgot-password", response_class=HTMLResponse)
async def get_forgot_password(request: Request):
    return templates.TemplateResponse(
        "pages/forgot-password.jinja",
        {"request": request, "active_page": "forgot-password"},
    )


@router.post("/forgot-password", response_class=HTMLResponse)
async def post_forgot_password(request: Request, forgot_password=ForgotPassword):
    match forgot_password:
        case _:
            return templates.TemplateResponse(
                "pages/forgot-password.jinja",
                {
                    "request": request,
                    "info": "An email with instructions was sent to the supplied email address.",
                    "active_page": "forgot-password",
                },
            )

@router.get("/reset-password", response_class=HTMLResponse)
async def get_reset_password(request: Request, token: str = Query()):
    return templates.TemplateResponse(
        "pages/reset-password.jinja",
        {"request": request, "token": token}
    )

@router.post("/reset-password", response_class=HTMLResponse)
async def post_reset_password(request: Request, reset_password=ResetPassword):
    match reset_password:
        case ResetPasswordRes.NO_TOKEN_FOUND | ResetPasswordRes.FOUND_TOKEN_EXPIRED:
            return templates.TemplateResponse(
                "pages/reset-password.jinja",
                {"request": request, "expired": True}
            )
        case ResetPasswordRes.NO_USER_FOUND | ResetPasswordRes.PARSING_ERROR:
            return templates.TemplateResponse(
                "pages/reset-password.jinja",
                {"request": request, "error": True}
            )
        case ResetPasswordRes.SUCCESS:
            return templates.TemplateResponse(
                "pages/reset-password.jinja",
                {"request": request, "success": True}
            )