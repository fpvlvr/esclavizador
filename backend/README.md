# Esclavizador Backend

Time tracking system backend API built with FastAPI, Tortoise ORM, and PostgreSQL.

## Tech Stack

- **Python:** 3.13
- **Framework:** FastAPI 0.121.1
- **ORM:** Tortoise ORM 0.25.1
- **Database:** PostgreSQL 16
- **Migrations:** Aerich 0.9.2
- **Auth:** JWT (PyJWT 2.10.1)
- **Dependency Management:** Poetry 2.2.1

## Prerequisites

- Python 3.13
- Poetry 2.2.1 ([installation guide](https://python-poetry.org/docs/#installation))
- Docker & Docker Compose (for PostgreSQL)

## Quick Start

### 1. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
cd backend
poetry install
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your SECRET_KEY (must be at least 32 characters)
# You can generate a secure key with:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start PostgreSQL

```bash
# From project root
cd ..
docker-compose up -d

# Verify PostgreSQL is running
docker-compose ps
```

### 4. Run Development Server

```bash
cd backend

# Option 1: Using poetry run (recommended)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Activate virtual environment manually
source $(poetry env info --path)/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   ├── deps.py                # Route dependencies (future)
│   │   └── v1/                    # API version 1
│   │       └── __init__.py
│   │
│   ├── core/                      # Configuration & utilities
│   │   ├── __init__.py
│   │   ├── config.py              # Settings management
│   │   └── database.py            # Tortoise ORM config
│   │
│   ├── models/                    # Tortoise ORM models (future)
│   ├── schemas/                   # Pydantic models (future)
│   ├── repositories/              # Database access layer (future)
│   ├── services/                  # Business logic (future)
│   └── integrations/              # External services (future)
│
├── tests/                         # Test suite (future)
├── migrations/                    # Aerich migrations (future)
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Poetry dependencies
└── README.md
```

## Poetry Commands

### Dependency Management

```bash
# Add a dependency
poetry add <package>

# Add a dev dependency
poetry add --group dev <package>

# Remove a dependency
poetry remove <package>

# Update dependencies
poetry update

# Show installed packages
poetry show
poetry show --tree
```

### Running Commands

```bash
# Run command in virtual environment (recommended)
poetry run <command>

# Activate virtual environment manually (Poetry 2.0+)
# For bash/zsh:
source $(poetry env info --path)/bin/activate
# For fish:
source $(poetry env info --path)/bin/activate.fish

# Common commands
poetry run pytest tests/ -v
poetry run black app/ tests/
poetry run ruff check app/ tests/
poetry run mypy app/
```

## Database Migrations (Aerich)

Migrations will be set up in Phase 2. Here's a preview:

```bash
# Initialize Aerich (run once)
poetry run aerich init -t app.core.database.TORTOISE_ORM

# Initialize database (creates tables)
poetry run aerich init-db

# Create a migration after model changes
poetry run aerich migrate --name "description"

# Apply migrations
poetry run aerich upgrade

# Rollback migration
poetry run aerich downgrade
```

## Development

### Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Note: Use postgres:// not postgresql:// for Tortoise ORM
DATABASE_URL=postgres://user:password@localhost:5432/esclavizador
SECRET_KEY=your-super-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=True
```

### Code Quality

```bash
# Format code with Black
poetry run black app/ tests/

# Lint with Ruff
poetry run ruff check app/ tests/
poetry run ruff check --fix app/ tests/

# Type check with mypy
poetry run mypy app/

# Run all checks
poetry run black app/ tests/ && \
poetry run ruff check app/ tests/ && \
poetry run mypy app/
```

### Testing

```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ -v --cov=app

# Run specific test file
poetry run pytest tests/test_api/test_auth.py -v

# Generate HTML coverage report
poetry run pytest tests/ -v --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Troubleshooting

### "poetry shell" command not found

**Issue:** Poetry 2.0+ removed the `shell` command by default.

**Solutions:**
```bash
# Option 1: Activate virtual environment manually (recommended)
source $(poetry env info --path)/bin/activate

# Option 2: Use poetry run for all commands
poetry run uvicorn app.main:app --reload

# Option 3: Install shell plugin if needed
# See: https://python-poetry.org/docs/managing-environments/#activating-the-environment
```

### Poetry uses wrong Python version

```bash
# Specify Python version
poetry env use python3.13
poetry env use /path/to/python3.13

# Check current environment
poetry env info
```

### Database connection issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Clear Poetry cache

```bash
poetry cache clear pypi --all
poetry install
```

## Next Steps

Phase 1 is complete! Next phases will add:

- **Phase 2:** Database models and migrations
- **Phase 3:** Authentication system (JWT)
- **Phase 4:** Project & Task management
- **Phase 5:** Time tracking functionality
- **Phase 6:** Tagging system
- **Phase 7:** Testing and documentation

See [/ai/implementation-plan.md](/ai/implementation-plan.md) for the complete roadmap.

## License

Proprietary - Internal use only
