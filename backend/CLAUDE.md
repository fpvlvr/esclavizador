# Code commenting
IMPORTANT: Always use this rule when you create new or modify existing code
- Code comments/docstrings should explain edge cases or non-obvious details
- Do not create self-evident docstrings

# Documentation Guidelines
IMPORTANT: Always use this rule when asked to document the progress/implementation details/current featureNo state

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
