# Code commenting
IMPORTANT: Always use this rule when you create new or modify existing code
- Code comments/docstrings should explain edge cases or non-obvious details
- Do not create self-evident docstrings

# Documentation Guidelines
IMPORTANT: Always use this rule when asked to document the progress/implementation details/current feature state

**Audience:** Claude (you) after context reset
**Purpose:** Enable picking up work seamlessly

---

## Core Principle

Documentation is a **map to code**, not a duplicate.

Test: "Does this help me continue work after context loss?"
→ Yes = keep concise / No = delete

---

## Include

- Architecture patterns (how layers connect, critical rules)
- File paths (where implementations live)
- Critical gotchas (non-obvious behaviors, security rules)
- Test organization (structure, fixture patterns)

---

## Exclude

- History (what was "fixed", versions, dates, bug stories)
- Metadata (test counts, status badges, timestamps)
- Code implementations (reference paths instead)
- Speculation (future features, might-do-later)

---

## Format

**Prefer:** Bullets, lists, dense

**Code:** Never copy project code → reference paths
**Exception:** Minimal pattern examples OK (e.g., dict unpacking)

**Example:**

```
❌ BAD:
We use TypedDict because it provides type safety while...

✅ GOOD:
Entities: TypedDict in `app/domain/entities.py`
Rule: Repository returns TypedDict, never ORM objects
```

---

## Quick Reference

What makes good docs:
- Scannable in seconds
- Points to code, doesn't duplicate it
- No historical baggage
- Actionable patterns, not explanations

---

# API Client Synchronization

## Automated Process

**Pre-commit hook:** `.husky/pre-commit`
- Detects backend `*.py` changes → exports OpenAPI spec + generates client
- Detects `openapi.json` changes → generates client only
- Auto-stages generated files
- Fast-path: skips if no backend changes (~0.1s)

**CI validation:** `.github/workflows/apiclient-check.yml`
- Runs on every PR and push to main
- Regenerates from scratch, compares with committed files
- Fails if out of sync

## Files

**Backend:**
- Export script: `backend/scripts/export_openapi.py`
- Schema: `backend/openapi.json` (committed)

**Frontend:**
- Generator: `@hey-api/openapi-ts` in `package.json`
- Generated: `frontend/esclavizador/lib/api/generated/` (committed)
- Custom wrapper: `frontend/esclavizador/lib/api/client.ts` (auth, tokens)

## Manual Regeneration

```bash
# Export OpenAPI spec
cd backend && poetry run python scripts/export_openapi.py

# Generate TypeScript client
cd frontend/esclavizador && npm run generate-client
```

## Troubleshooting

**Hook fails "poetry not found":**
- Install: https://python-poetry.org/docs/#installation

**Hook fails "npm not found":**
- Install Node.js: https://nodejs.org/

**Hook fails with Python error:**
- Run: `cd backend && poetry install`
- Test: `poetry run python -c 'from app.main import app'`

**Hook fails with npm error:**
- Run: `cd frontend/esclavizador && npm install`
- Test: `npm run generate-client`

**CI fails "client out of sync":**
- Regenerate locally (see Manual Regeneration above)
- Pre-commit hook may have been bypassed

## Bypass Options

```bash
# Force regeneration (even if no changes detected)
FORCE_CODEGEN=1 git commit

# Emergency skip (not recommended)
SKIP_HOOKS=1 git commit
git commit --no-verify
```

## How It Works

**Developer workflow:**
1. Modify backend API (e.g., `backend/app/api/v1/auth/auth.py`)
2. Stage changes: `git add backend/`
3. Commit: `git commit -m "feat: add endpoint"`
4. Hook detects `*.py` changes
5. Auto-exports OpenAPI spec
6. Auto-generates TypeScript client
7. Auto-stages both files
8. Commit includes all changes

**Performance:**
- No backend changes: ~0.1s (fast path)
- Export spec: ~2-3s
- Export + generate: ~5-8s
