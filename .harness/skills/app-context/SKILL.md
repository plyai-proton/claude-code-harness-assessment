# Skill: App Context

Shared foundation skill — read by every agent (Planner, Generator, Evaluator, Monitor)
before acting. Describes what StoreOps *is*, not how to build or grade it.

## What StoreOps is

A REST API for retail store operations management. Every entity belongs to exactly one
`store_id`; there is no cross-store visibility in the current design. Storage is
in-memory, process-lifetime only (no database) — each module owns one repository
singleton instantiated at import time.

## Modules implemented today

| Module | Path | Owns | Has HTTP routes? |
|---|---|---|---|
| `activities` | `app/activities/` | `Task` | Yes |
| `programmes` | `app/programmes/` | `Project`, `ProjectMember` | Yes |
| `staff` | `app/staff/` | `User`, `AuthToken` | **No** — auth-only, no CRUD surface |
| `alerts` | `app/alerts/` | `Notification` | Yes (read-only: `GET` only) |

`reports` does **not** exist yet. Per the case study (Section 3.6), it is added later as a
demonstration feature and is read-only by design — it aggregates data across the other
modules but must never write to them. Do not scaffold `reports` speculatively; build it
only when a sprint contract explicitly calls for it.

## Entities and enums (exact, current)

**activities** (`app/activities/models.py`):
- `Task`: `id, title, description, status, priority, category, store_id, programme_id, owner_id, assignee_id, created_at, updated_at`
- `TaskStatus`: `TODO | IN_PROGRESS | DONE | BLOCKED`
- `TaskPriority`: `LOW | MEDIUM | HIGH | CRITICAL`
- `TaskCategory`: `RESTOCKING | PLANOGRAM | AUDIT | COMPLIANCE | GENERAL`

**programmes** (`app/programmes/models.py`):
- `Project`: `id, name, description, store_id, created_at`
- `ProjectMember`: `project_id, user_id, role`
- `ProjectRole`: `STORE_MANAGER | DEPARTMENT_LEAD | ASSOCIATE`

**staff** (`app/staff/models.py`):
- `User`: `id, name, email, store_id, role`
- `AuthToken`: `token, user_id`
- `StaffRole`: `REGIONAL_MANAGER | STORE_MANAGER | DEPARTMENT_LEAD | ASSOCIATE`

**alerts** (`app/alerts/models.py`):
- `Notification`: `id, type, channel, status, recipient_id, store_id, message, related_entity_id, created_at`
- `AlertType`: `INVENTORY | SLA_BREACH | SHIFT_HANDOVER | ESCALATION`
- `NotificationChannel`: `IN_APP | EMAIL`
- `NotificationStatus`: `PENDING | SENT | READ | FAILED`

## Auth model (stub — this is a reference project, not production auth)

`app/shared/auth.py`'s `get_current_user` dependency resolves a `Bearer <token>`
`Authorization` header via `app.staff.service.authenticate`. Three users are seeded in
`app/staff/repository.py`, all in `store-1`:

| Token | User | Role |
|---|---|---|
| `dev-token-store-manager` | `user-1` (Alex Rivera) | `STORE_MANAGER` |
| `dev-token-associate` | `user-2` (Jordan Lee) | `ASSOCIATE` |
| `dev-token-department-lead` | `user-3` (Sam Patel) | `DEPARTMENT_LEAD` |

There is no `REGIONAL_MANAGER` seed user yet — add one if a sprint needs to exercise that
role.

## Endpoints implemented today

```
GET    /health
GET    /api/activities            (filters: programme_id, status)
POST   /api/activities
GET    /api/activities/{id}
PATCH  /api/activities/{id}       (status, priority, category, assignee_id)
DELETE /api/activities/{id}       (owner or STORE_MANAGER/REGIONAL_MANAGER only)
GET    /api/programmes
POST   /api/programmes
POST   /api/programmes/{id}/members
GET    /api/alerts
```

## Cross-module wiring that already exists

`app/shared/event_bus.py` provides a process-wide `event_bus` singleton. `alerts` already
subscribes to a `"notification.requested"` event (registered in
`app.alerts.service.register_event_handlers()`, wired at app startup in `app/main.py`).
Any module that needs to create a notification as a side effect of its own action must
`event_bus.emit("notification.requested", {...})` — never import
`app.alerts.service.create_notification` directly. See `architecture-principles/SKILL.md`
for why.

## Running and checking the project

```
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/mypy .
.venv/bin/ruff check .
.venv/bin/pytest --cov=app --cov-report=term-missing
.venv/bin/python scripts/check_architecture.py
.venv/bin/uvicorn app.main:app --reload   # http://localhost:8000
```
