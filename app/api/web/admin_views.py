from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.athlete import Athlete
from app.models.coach import Coach
from app.models.competition import Competition
from app.models.result import Result
from app.models.user import User, UserRole
from app.services import admin_service
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/admin", tags=["web-admin"])
templates = Jinja2Templates(directory="app/templates")


async def _require_admin(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("role") != "admin":
            return None
        user_id = int(payload["sub"])
    except Exception:
        return None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = await _require_admin(request)
    if not user:
        return RedirectResponse("/login")

    emb: EmbeddingService = request.app.state.embedding_service
    async with AsyncSessionLocal() as db:
        stats = await admin_service.get_stats(db, emb)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": user, "stats": stats, "active": "admin", "active_tab": "dashboard"},
    )


@router.post("/index/rebuild")
async def rebuild_index_web(request: Request):
    user = await _require_admin(request)
    if not user:
        return RedirectResponse("/login")
    emb: EmbeddingService = request.app.state.embedding_service
    async with AsyncSessionLocal() as db:
        await emb.build_full_index(db)
    return RedirectResponse("/admin", status_code=303)


@router.get("/athletes", response_class=HTMLResponse)
async def admin_athletes(request: Request, sport_type: str = None, region: str = None, page: int = 1):
    user = await _require_admin(request)
    if not user:
        return RedirectResponse("/login")

    page_size = 20
    async with AsyncSessionLocal() as db:
        from sqlalchemy.orm import selectinload
        q = select(Athlete).options(selectinload(Athlete.coach))
        if sport_type: q = q.where(Athlete.sport_type.ilike(f"%{sport_type}%"))
        if region: q = q.where(Athlete.region.ilike(f"%{region}%"))
        from sqlalchemy import func
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()

    import math
    return templates.TemplateResponse(
        "admin/athletes.html",
        {
            "request": request, "user": user, "athletes": rows, "active": "admin",
            "active_tab": "athletes", "page": page, "pages": math.ceil(total/page_size) if total else 1,
            "filters": {"sport_type": sport_type, "region": region},
            "access_token": request.cookies.get("access_token", ""),
        },
    )


@router.get("/coaches", response_class=HTMLResponse)
async def admin_coaches(request: Request):
    user = await _require_admin(request)
    if not user: return RedirectResponse("/login")
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(select(Coach))).scalars().all()
    return templates.TemplateResponse(
        "admin/coaches.html",
        {"request": request, "user": user, "coaches": rows, "active": "admin",
         "active_tab": "coaches", "access_token": request.cookies.get("access_token", "")},
    )


@router.get("/competitions", response_class=HTMLResponse)
async def admin_competitions(request: Request):
    user = await _require_admin(request)
    if not user: return RedirectResponse("/login")
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(select(Competition).order_by(Competition.date.desc()))).scalars().all()
    return templates.TemplateResponse(
        "admin/competitions.html",
        {"request": request, "user": user, "competitions": rows, "active": "admin",
         "active_tab": "competitions", "access_token": request.cookies.get("access_token", "")},
    )


@router.get("/results", response_class=HTMLResponse)
async def admin_results(request: Request):
    user = await _require_admin(request)
    if not user: return RedirectResponse("/login")
    async with AsyncSessionLocal() as db:
        from sqlalchemy.orm import selectinload
        rows = (
            await db.execute(
                select(Result)
                .options(selectinload(Result.athlete), selectinload(Result.competition))
                .order_by(Result.year.desc())
                .limit(100)
            )
        ).scalars().all()
    return templates.TemplateResponse(
        "admin/results.html",
        {"request": request, "user": user, "results": rows, "active": "admin",
         "active_tab": "results", "access_token": request.cookies.get("access_token", "")},
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    user = await _require_admin(request)
    if not user: return RedirectResponse("/login")
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(select(User))).scalars().all()
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "user": user, "users": rows, "active": "admin",
         "active_tab": "users", "access_token": request.cookies.get("access_token", "")},
    )
