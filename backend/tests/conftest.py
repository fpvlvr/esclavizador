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
from app.models.user import UserRole
from app.core.security import hash_password
from app.repositories.user_repo import user_repo
from app.repositories.organization_repo import organization_repo
from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


@pytest.fixture(scope="session")
def test_worker_email():
    """Email for test_worker fixture."""
    return "worker@example.com"


@pytest.fixture(scope="session")
def test_worker_password():
    """Password for test_worker fixture."""
    return "WorkerPass123!"


@pytest.fixture(scope="session")
def test_boss_email():
    """Email for test_boss fixture."""
    return "boss@example.com"


@pytest.fixture(scope="session")
def test_boss_password():
    """Password for test_boss fixture."""
    return "BossPass123!"


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
        OrganizationData dict with name "Test Org"
    """
    org = await organization_repo.create_organization(name="Test Org")
    yield org
    await organization_repo.delete(org["id"])


@pytest_asyncio.fixture
async def test_worker(test_org, test_worker_email, test_worker_password):
    """
    Create test user with WORKER role.

    Credentials:
        email: worker@example.com (from test_worker_email fixture)
        password: WorkerPass123! (from test_worker_password fixture)
        role: WORKER

    Args:
        test_org: Organization fixture (OrganizationData dict)
        test_worker_email: Email fixture
        test_worker_password: Password fixture

    Returns:
        UserData dict
    """
    user = await user_repo.create_user(
        email=test_worker_email,
        password_hash=hash_password(test_worker_password),
        role=UserRole.WORKER,
        organization_id=test_org["id"]
    )
    yield user
    await user_repo.delete(user["id"])


@pytest_asyncio.fixture
async def test_boss(test_org, test_boss_email, test_boss_password):
    """
    Create test user with BOSS role.

    Credentials:
        email: boss@example.com (from test_boss_email fixture)
        password: BossPass123! (from test_boss_password fixture)
        role: BOSS

    Args:
        test_org: Organization fixture (OrganizationData dict)
        test_boss_email: Email fixture
        test_boss_password: Password fixture

    Returns:
        UserData dict
    """
    user = await user_repo.create_user(
        email=test_boss_email,
        password_hash=hash_password(test_boss_password),
        role=UserRole.BOSS,
        organization_id=test_org["id"]
    )
    yield user
    await user_repo.delete(user["id"])


@pytest_asyncio.fixture
async def test_project(test_org):
    """
    Create test project via repository.

    Args:
        test_org: Organization fixture (OrganizationData dict)

    Returns:
        ProjectData dict
    """
    project = await project_repo.create(
        name="Test Project",
        description="Test project description",
        org_id=test_org["id"]
    )
    yield project
    await project_repo.delete(project["id"])


@pytest_asyncio.fixture
async def test_task(test_project):
    """
    Create test task via repository.

    Args:
        test_project: Project fixture (ProjectData dict)

    Returns:
        TaskData dict
    """
    task = await task_repo.create(
        name="Test Task",
        description="Test task description",
        project_id=test_project["id"]
    )
    yield task
    await task_repo.delete(task["id"])


@pytest_asyncio.fixture
async def second_org():
    """
    Create second organization for multi-tenant isolation tests.

    Returns:
        OrganizationData dict with name "Second Org"
    """
    org = await organization_repo.create_organization(name="Second Org")
    yield org
    await organization_repo.delete(org["id"])


@pytest_asyncio.fixture
async def second_org_project(second_org):
    """
    Create project in second organization for isolation tests.

    Args:
        second_org: Second organization fixture (OrganizationData dict)

    Returns:
        ProjectData dict in second_org
    """
    project = await project_repo.create(
        name="Second Org Project",
        description=None,
        org_id=second_org["id"]
    )
    yield project
    await project_repo.delete(project["id"])
