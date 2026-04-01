"""
Shared pytest fixtures for Claim360 backend tests.

Uses an in-memory SQLite database so tests run without a DB server.
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Ensure the backend package root is importable
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# Override settings BEFORE any app code touches the real database
# ---------------------------------------------------------------------------
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["DATABASE_URL_SYNC"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"
os.environ["BASE_URL"] = "http://testserver"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["ADMIN_EMAIL"] = ""
os.environ["ADMIN_PASSWORD"] = ""
os.environ["GOOGLE_CLIENT_ID"] = "fake-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "fake-client-secret"

# Clear lru_cache so settings pick up our env overrides
from core.config import get_settings
get_settings.cache_clear()

from core.database import Base, get_db
from core.auth import create_access_token, get_password_hash
from models.user import User, OTP, AppSettings, Campaign, Template, Contact

# ---------------------------------------------------------------------------
# Async SQLite engine shared across a single test session
# ---------------------------------------------------------------------------
TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a fresh DB session for direct DB manipulation in tests."""
    async with TestSessionLocal() as session:
        yield session


async def _override_get_db():
    """FastAPI dependency override that uses the test database."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """HTTP test client wired to the FastAPI app with test DB."""
    from main import app
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Helper: seed a user and return (user_obj, token_str) ──────────────────
async def _seed_user(
    db: AsyncSession,
    email: str,
    password: str = "testpass123",
    full_name: str = "Test User",
    is_admin: bool = False,
    is_active: bool = True,
) -> tuple:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_admin=is_admin,
        is_active=is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return user, token


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    """Create a regular (non-admin) active user. Returns (User, token)."""
    return await _seed_user(db_session, "user@test.com")


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin active user. Returns (User, token)."""
    return await _seed_user(
        db_session, "admin@test.com", is_admin=True, full_name="Admin User"
    )


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession):
    """Create an inactive user. Returns (User, token)."""
    return await _seed_user(
        db_session, "inactive@test.com", is_active=False
    )


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession):
    """A second regular user for cross-user permission tests."""
    return await _seed_user(
        db_session, "user2@test.com", full_name="Second User"
    )


@pytest_asyncio.fixture
async def app_settings_open(db_session: AsyncSession):
    """Seed AppSettings with registrations open."""
    row = AppSettings(registrations_open=True)
    db_session.add(row)
    await db_session.commit()
    return row


@pytest_asyncio.fixture
async def app_settings_closed(db_session: AsyncSession):
    """Seed AppSettings with registrations closed."""
    row = AppSettings(registrations_open=False)
    db_session.add(row)
    await db_session.commit()
    return row


def auth_header(token: str) -> dict:
    """Build Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}
