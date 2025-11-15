"""
Test fixtures and configuration for pytest.

Provides:
- Test database initialization with SQLite in-memory
- HTTP client fixture for API testing
- Reusable test data fixtures (organizations, users)

Uses the official Tortoise ORM testing pattern with initializer/finalizer
for proper event loop management.

Sources:
- https://tortoise.github.io/contrib/unittest.html
- https://github.com/tortoise/tortoise-orm/blob/develop/conftest.py
"""

import pytest
import pytest_asyncio
from tortoise import Tortoise
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.core.security import hash_password


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for session-scoped async fixtures.

    This override is needed because we're using session-scoped
    database initialization, which requires a session-scoped loop.

    Note: pytest-asyncio will warn about this custom fixture,
    but it's necessary for our testing architecture.
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    # Ensure proper cleanup
    try:
        # Cancel all pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        # Run loop one last time to process cancellations
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    finally:
        loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_tests():
    """
    Initialize test database once per test session.

    The database is created once and shared across all tests
    for performance. Individual tests should clean up their
    own data using function-scoped fixtures.
    """
    # Initialize with explicit configuration
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models"]}
    )
    # Generate database schema
    await Tortoise.generate_schemas()
    yield
    # Cleanup
    await Tortoise._drop_databases()
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client for testing FastAPI endpoints.

    Usage:
        async def test_endpoint(client):
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 200
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_org():
    """
    Create test organization.

    Returns:
        Organization instance with name "Test Org"
    """
    org = await Organization.create(name="Test Org")
    yield org
    await org.delete()


@pytest_asyncio.fixture
async def test_user(test_org):
    """
    Create test user with SLAVE role.

    Credentials:
        email: test@example.com
        password: TestPass123!
        role: SLAVE

    Args:
        test_org: Organization fixture

    Returns:
        User instance
    """
    user = await User.create(
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.SLAVE,
        organization=test_org,
        is_active=True
    )
    yield user
    await user.delete()


@pytest_asyncio.fixture
async def test_master(test_org):
    """
    Create test user with MASTER role.

    Credentials:
        email: master@example.com
        password: MasterPass123!
        role: MASTER

    Args:
        test_org: Organization fixture

    Returns:
        User instance
    """
    user = await User.create(
        email="master@example.com",
        password_hash=hash_password("MasterPass123!"),
        role=UserRole.MASTER,
        organization=test_org,
        is_active=True
    )
    yield user
    await user.delete()
