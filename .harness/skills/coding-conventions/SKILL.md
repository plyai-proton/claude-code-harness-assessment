# Skill: Coding Conventions

Generator-specific skill. StoreOps is Python 3.11+ / FastAPI. These conventions are
enforced by `mypy --strict` and `ruff` (`pyproject.toml`) plus the patterns already
established in the baseline scaffold — follow the existing code, don't introduce a
competing style.

## Module layout (per module: `activities`, `programmes`, `staff`, `alerts`, future `reports`)

```
app/<module>/
  __init__.py       # empty
  models.py         # pydantic BaseModel entities + StrEnum value types
  repository.py     # in-memory data access, one singleton instance at module scope
  service.py        # business logic; the module's public cross-module read interface
  routes.py         # FastAPI APIRouter; omitted entirely for auth-only modules (staff)
```

## Typing

`mypy --strict` is in force — every function needs full type annotations, no implicit
`Any`. Use `from __future__ import annotations` at the top of every file (already the
convention throughout `app/`). Use `X | None`, not `Optional[X]`. Use `list[X]`/`dict[K, V]`
generics directly, not `typing.List`/`typing.Dict`.

## Enums and entities

Value types are `StrEnum` (not plain `str` constants, not `IntEnum`) — see
`TaskStatus`, `TaskPriority`, `TaskCategory` in `app/activities/models.py` for the
pattern. Entities are pydantic `BaseModel`s. A create/update payload gets its own model
(`TaskCreate`, `TaskUpdate`) rather than reusing the entity model with all-optional
fields — this keeps the API contract explicit and keeps `routes.py` validation-only.

## Repository pattern

One singleton instance per module, created at the bottom of `repository.py`
(`activity_repository = ActivityRepository()`), imported by that module's `service.py`
only. Internal storage is a `dict[str, T]` keyed by generated ID
(`f"{prefix}-{counter}"`, see `ActivityRepository.generate_id`). Never expose the raw
dict — every access goes through a typed method (`get`, `list_by_store`, `create`,
`update`, `delete`).

## Error handling — the AppError pattern

```python
from app.shared.errors import NotFoundError, ValidationError

def get_activity(task_id: str, store_id: str) -> Task:
    task = activity_repository.get(task_id)
    if task is None or task.store_id != store_id:
        raise NotFoundError(f"Activity {task_id} not found")
    return task
```

Never `raise Exception(...)` or any other builtin exception from `service.py` or
`routes.py` — this is a hard gate (`ruff check --select TRY002`), not a style preference.
`app/main.py` already registers a single `AppError` exception handler that converts any
subclass into `{"code": ..., "message": ...}` with the right HTTP status — you never need
to catch `AppError` yourself in a route.

## FastAPI dependency injection

Use the `Annotated` pattern already established (avoids `ruff`'s B008 on `Depends()` in a
default value):

```python
from typing import Annotated
from fastapi import Depends
from app.shared.auth import get_current_user
from app.staff.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/{task_id}", response_model=Task)
def get_activity(task_id: str, user: CurrentUser) -> Task:
    ...
```

Define `CurrentUser` once per `routes.py` module (not inline per-endpoint).

## Cross-module calls

- **Read** another module's data → import and call its `service.py` function
  (`from app.staff.service import get_user_by_id`), never its `repository.py`.
- **Trigger a side effect** in another module → `event_bus.emit(event_name, payload)` from
  `app.shared.event_bus`, never call the other module's service mutator directly. See
  `app/alerts/service.py`'s `register_event_handlers()` for the subscriber-side pattern to
  mirror when a new module needs to react to events.

## Imports and formatting

`ruff`'s `I` (isort) rule enforces import order — standard library, then third-party, then
local `app.*`, each group alphabetized; just run `ruff check --fix .` rather than ordering
by hand. Line length is 100 (`pyproject.toml`); prefer breaking a call's arguments onto
their own lines over a trailing long line.

## Timestamps

Use `datetime.now(UTC)` (imported as `from datetime import UTC, datetime`), never the
deprecated `datetime.utcnow()`.
