import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    Session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session, mocker):
    # Mock embedding service (no OpenAI key needed in tests)
    mocker.patch(
        "app.services.embedding_service.EmbeddingService.initialize",
        return_value=None,
    )
    mocker.patch(
        "app.services.embedding_service.EmbeddingService.search",
        return_value=[],
    )

    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session):
    user = User(
        username="testadmin",
        email="testadmin@test.com",
        hashed_password=hash_password("Test@123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin", "password": "Test@123"},
    )
    return resp.json()["access_token"]
