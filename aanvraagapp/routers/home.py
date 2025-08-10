from fastapi import APIRouter, Depends, Request
from ..controllers import HomeController

router = APIRouter()


@router.get("/home")
async def get_home_page(
    request: Request,
    c: HomeController = Depends(HomeController)
):
    return await c.get_home()
    # return templates.TemplateResponse(
    #     "pages/home.jinja", 
    #     {
    #         "request": request, 
    #         "current_user": current_user, 
    #         "greeting": home_data,
    #         "active_page": "home"
    #     }
    # )