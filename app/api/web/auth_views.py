from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.security import create_access_token, create_refresh_token
from app.core.database import AsyncSessionLocal
from app.services.auth_service import authenticate_user

router = APIRouter(tags=["web-auth"])
templates = Jinja2Templates(directory="app/templates")

REFRESH_COOKIE = "refresh_token"
ACCESS_COOKIE = "access_token"


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    async with AsyncSessionLocal() as db:
        try:
            user, access_token, refresh_token = await authenticate_user(
                db, username, password, ip=request.client.host if request.client else None
            )
            await db.commit()
        except Exception:
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "Username yoki parol noto'g'ri"},
                status_code=401,
            )

    resp = RedirectResponse(url="/chat", status_code=303)
    resp.set_cookie(ACCESS_COOKIE, access_token, httponly=True, samesite="lax", max_age=1800)
    resp.set_cookie(REFRESH_COOKIE, refresh_token, httponly=True, samesite="lax", max_age=7*24*3600)
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(ACCESS_COOKIE)
    resp.delete_cookie(REFRESH_COOKIE)
    return resp
