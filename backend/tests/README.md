# Test Architecture

## Core Principles

### ORM Isolation
**Repositories are the ONLY layer that touches ORM models.**

- ✅ Tests use repositories: `user_repo.create_user()`, `project_repo.get_by_id()`
- ✅ Tests work with TypedDict entities: `UserData`, `ProjectData`, `TaskData`
- ❌ Never import ORM models in tests: `from app.models.user import User`
- ❌ Never use ORM methods: `user.save()`, `Project.create()`

All data returned from repositories are plain dicts, not ORM objects.

### Fixture Pattern

**Prerequisites use fixtures. Test subjects are created in-test.**

- **Prerequisite**: Something needed for the test but not being tested
  - Use fixture: `test_org`, `test_project`, `test_task`
  - Example: `test_api/test_projects.py:232` - uses `test_project` to test GET endpoint

- **Test Subject**: The thing being created/tested
  - Create in-test with specific data
  - Example: `test_api/test_projects.py:378` - creates project to test DELETE

See `conftest.py` for available fixtures.

## Fixtures

### User Fixtures
- `test_worker` - WORKER role user
- `test_boss` - BOSS role user

### Credential Fixtures (Single Source of Truth)
- `test_worker_email` → `"worker@example.com"`
- `test_worker_password` → `"WorkerPass123!"`
- `test_boss_email` → `"boss@example.com"`
- `test_boss_password` → `"BossPass123!"`

Always use credential fixtures in tests, never hardcode.

**Example**: `test_api/test_auth.py:166-170` - login test using credential fixtures

### Entity Fixtures
- `test_org` - Organization (prerequisite)
- `test_project` - Project in test_org
- `test_task` - Task in test_project
- `second_org` - Second organization (for isolation tests)
- `second_org_project` - Project in second_org

## Common Patterns

### Repository Usage
See `test_repositories/` for repository layer tests.
See `test_services/test_task_service.py:67-85` for creating/cleaning up test data.

### API Tests with Authentication
See `test_api/test_tasks.py:97-119` - pattern for login + authenticated request.

### Multi-tenant Isolation
See `test_api/test_projects.py:197-226` - pattern for testing cross-org access returns 404.

### Soft Delete Verification
See `test_api/test_projects.py:377-407` - pattern for verifying soft delete (is_active=False).

## Key Technical Details

### UUID Handling
- Repositories accept `UUID | str` - no str() casts needed
- **Exception**: JWT encoding requires str() - see `test_api/test_auth.py:258`

### Role Values
- UserRole enum stores lowercase: `"boss"`, `"worker"`
- Check `app/models/user.py:11-14` for enum definition
- Fixed bug: `app/api/deps.py:125` uses lowercase `"boss"` not `"BOSS"`

## Test Organization

```
tests/
├── test_repositories/  # Repository layer (ORM → TypedDict)
├── test_services/      # Business logic (auth, validation, multi-tenant)
└── test_api/           # HTTP endpoints (full request/response cycle)
```

Each layer tests its own concerns. Higher layers use repositories, never ORM.
