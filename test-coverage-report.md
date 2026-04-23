# Test Coverage Report

Baseline coverage before this session: ~60%
Coverage after adding tests: **68%** (172 passed, 2 skipped)

---

## 1. Schema: NULL values from DB rejected by strict Pydantic fields

**Class:** Data validation / schema definition
**Severity:** High — causes HTTP 500 on otherwise valid list endpoints

### Affected fields

| Schema | Field | Fix applied |
|--------|-------|-------------|
| `RouteSchema` | `color: str` | `@field_validator("color", mode="before")` coerces `None → ""` |
| `QuestionnaireSchema` | `max_score: int` | `@field_validator("max_score", mode="before")` coerces `None → 0` |

### Root cause

The DB columns allow NULL, but the Pydantic v2 schemas declare the
fields as non-optional (`str`, `int`). Pydantic v2 does not coerce
`None` to a default; it raises a `ValidationError`. Any list endpoint
that encounters a row with a NULL in these columns returns HTTP 500.

### Recommendation

Audit all schema fields that map to nullable DB columns and either:
- declare them `Optional[T]` / `T | None`, or
- add a `mode="before"` validator that maps `None` to a sensible
  default.

---

## 2. Missing error handler for `NotFound` exception

**Class:** Exception handling / HTTP error mapping
**Severity:** Medium — `NotFound` silently becomes HTTP 500

### Description

`powonline.exc.NotFound` is raised by core functions when a resource is
not found. There was no registered FastAPI exception handler for this
type, so it fell through to `handle_unhandled_exceptions` which returns
HTTP 500 instead of 404.

**Fix applied:** Added `handle_not_found` handler in
`src/powonline/error_handlers.py` registered for `exc.NotFound`.

### Recommendation

Review all custom exception types in `powonline/exc.py` and ensure each
has a registered handler with the correct HTTP status code.

---

## 3. Synchronous lazy-relationship access inside async handlers
   (MissingGreenlet)

**Class:** SQLAlchemy async / ORM usage
**Severity:** High — causes HTTP 500 for affected endpoints

### Affected endpoints

| Endpoint | Handler | Root cause |
|----------|---------|------------|
| `GET /events/{id}/station/{s}/users/{u}` | `is_user_assigned_to_station` | `user.stations` accessed synchronously in async context |

### Description

SQLAlchemy's async session does not allow synchronous access to lazy
relationships. Code that reads `obj.relationship` (without `await`) from
an async handler raises:

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called
```

The pattern needed is:

```python
# Wrong
if user.stations:

# Correct
stations = await user.awaitable_attrs.stations
if stations:
```

A similar bug existed in `core.Team.stations` (line 449 of `core.py`)
where `team.route` was read synchronously before being awaited. That
instance was trivially fixed during this session (the check was moved
after the `await`).

### Affected test

`test_is_user_assigned_to_station_true` and
`test_is_user_assigned_to_station_false` are currently **skipped** with
reason *"MissingGreenlet bug: lazy async relationship in sync context"*.

### Recommendation

Search the codebase for all direct relationship attribute accesses
inside `async def` functions and replace with `await
obj.awaitable_attrs.<rel>`. Consider enabling SQLAlchemy's
`lazy="raise_on_sql"` in tests to surface these issues at test time.

---

## 4. Test data: `seed_cleanup.sql` did not truncate `event` table

**Class:** Test infrastructure
**Severity:** Medium — stale rows with `NULL time_range` caused
`list_events` to crash with a Pydantic `ValidationError` in subsequent
tests when `event` rows were not cleaned up between runs.

**Fix applied:** Added `event` to the `TRUNCATE … CASCADE` statement in
`tests/seed_cleanup.sql`.

---

## Remaining low-coverage areas (not yet tested)

| Module | Coverage | Notes |
|--------|----------|-------|
| `resources/upload.py` | 28% | File-upload logic; requires multipart fixtures |
| `social.py` | 47% | OAuth social login flows |
| `mailfetcher.py` | 0% | Background mail-fetcher; likely needs mocking |
| `resources/job.py` | 58% | Several score-setting branches untested |
| `resources/station.py` | 57% | Create/update/delete station paths |
| `resources/user.py` | 57% | User mutation paths |
| `resources/assignment.py` | 56% | Only GET tested; mutation paths missing |
