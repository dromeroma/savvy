"""Shared test fixtures for SavvyCore integration tests."""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings
from src.core.database import Base
from src.core.dependencies import get_db
from src.core.security import create_access_token, hash_password
from src.main import create_app

# Import models so tables are registered on Base.metadata
from src.modules.auth.models import User, RefreshToken  # noqa: F401
from src.modules.organization.models import Organization, Membership, Invitation  # noqa: F401

settings = get_settings()

# Use a separate test database
TEST_DB_URL = settings.DATABASE_URL
if not TEST_DB_URL.endswith("_test"):
    TEST_DB_URL = TEST_DB_URL + "_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables before tests, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional DB session that rolls back after each test."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client wired to use the test DB session."""
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_org(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(
        id=uuid.uuid4(),
        name="Test Corp",
        slug="test-corp",
        type="business",
        settings={},
    )
    db_session.add(org)
    await db_session.flush()
    return org


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_org: Organization) -> User:
    """Create a test user with owner membership."""
    user = User(
        id=uuid.uuid4(),
        name="Test Owner",
        email="owner@test.com",
        password_hash=hash_password("Test1234!"),
    )
    db_session.add(user)
    await db_session.flush()

    membership = Membership(
        id=uuid.uuid4(),
        organization_id=test_org.id,
        user_id=user.id,
        role="owner",
    )
    db_session.add(membership)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
def auth_headers(test_user: User, test_org: Organization) -> dict[str, str]:
    """Authorization headers with a valid access token."""
    token = create_access_token(
        {
            "sub": str(test_user.id),
            "org_id": str(test_org.id),
            "role": "owner",
        }
    )
    return {"Authorization": f"Bearer {token}"}
