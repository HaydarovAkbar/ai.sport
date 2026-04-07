from fastapi import APIRouter

from app.api.v1 import admin, athletes, auth, chat, coaches, competitions, results

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(athletes.router)
api_router.include_router(coaches.router)
api_router.include_router(competitions.router)
api_router.include_router(results.router)
api_router.include_router(admin.router)
