from fastapi import APIRouter

from app.api.web import admin_views, auth_views, chat_views

web_router = APIRouter()

web_router.include_router(auth_views.router)
web_router.include_router(chat_views.router)
web_router.include_router(admin_views.router)
