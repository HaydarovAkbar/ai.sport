from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.api.web.router import web_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging_config import RequestLoggingMiddleware, setup_logging
from app.core.rate_limiter import limiter
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # ── OpenAI + services (used by web requests for non-job ops) ──
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    embedding_service = EmbeddingService(openai_client)
    async with AsyncSessionLocal() as db:
        await embedding_service.initialize(db)

    rag_service = RAGService(embedding_service, openai_client)
    chat_service = ChatService(rag_service)

    app.state.embedding_service = embedding_service
    app.state.rag_service = rag_service
    app.state.chat_service = chat_service

    # ── ARQ Redis pool ─────────────────────────────────────────────
    arq_pool = await create_pool(
        RedisSettings(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            database=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
        )
    )
    app.state.arq_pool = arq_pool

    yield

    # ── Shutdown ───────────────────────────────────────────────────
    await arq_pool.aclose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ── Static files ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Routers ───────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)
