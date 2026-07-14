import asyncio
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.user import User


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# In-memory SQLite async engine
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _create_tables():
    """Create all tables before each test, drop after."""
    # Import all models so Base.metadata is populated
    import app.models  # noqa: F401

    # pgvector Vector columns won't work on SQLite, so we patch the
    # column type to a plain TEXT before creating tables.
    from app.models.page import Page
    col = Page.__table__.c.embedding
    from sqlalchemy import Text as SAText
    col.type = SAText()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# DB session fixture
# ---------------------------------------------------------------------------

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Fake user
# ---------------------------------------------------------------------------

@pytest.fixture
async def fake_user(db: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        name="Test User",
        plan="free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# FastAPI test client with dependency overrides
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(db: AsyncSession, fake_user: User) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.dependencies import get_db, get_current_user

    async def _override_get_db():
        yield db

    async def _override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
