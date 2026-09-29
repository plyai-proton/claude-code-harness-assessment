# Skill: How to Test

Generator-specific skill. Testing conventions and coverage thresholds for StoreOps.
Directly addresses client failure mode 3 ("tests that asserted HTTP status codes but did
not verify business rule compliance") — the rule here is simple: **a status-code-only
assertion is never sufficient by itself.**

## Directory layout

Tests mirror `app/`'s module structure: `tests/<module>/test_routes.py` (HTTP-level,
via `TestClient`) and, where service logic has branches not fully exercised through HTTP
(authorization checks, validation edge cases), `tests/<module>/test_service.py`
(service-level, calling functions directly).

## Fixtures (from `tests/conftest.py` — reuse these, don't redefine)

- `client` — a `fastapi.testclient.TestClient` wrapping `app.main.app`, fresh per test.
- `auth_header(token: str) -> dict[str, str]` — builds the `Authorization: Bearer ...`
  header; use the seeded tokens from `app-context/SKILL.md`
  (`STORE_MANAGER_TOKEN`, `ASSOCIATE_TOKEN`, `DEPARTMENT_LEAD_TOKEN`, importable from
  `tests.conftest`).

For service-level tests against a module whose repository is a process-wide singleton,
add an `autouse` fixture that clears its internal store between tests — see
`tests/activities/test_service.py`'s `_reset_repository` for the pattern:

```python
@pytest.fixture(autouse=True)
def _reset_repository() -> None:
    activity_repository._tasks.clear()
    activity_repository._next_id = 1
```

## Asserting business rules, not just status codes

**Insufficient** (this is the exact pattern that produced client failure mode 3):

```python
def test_create_activity(client):
    resp = client.post("/api/activities", json={...}, headers=auth_header(TOKEN))
    assert resp.status_code == 201
```

**Required**: assert the status code *and* the specific field(s) the acceptance criterion
names:

```python
def test_delete_activity_requires_owner_or_manager(client):
    created = client.post("/api/activities", json={"title": "X"}, headers=auth_header(STORE_MANAGER_TOKEN)).json()
    forbidden = client.delete(f"/api/activities/{created['id']}", headers=auth_header(ASSOCIATE_TOKEN))
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "FORBIDDEN"   # the business rule, not just the code
```

When a sprint's acceptance criterion involves an event (`event_bus.emit`), assert the
*observable downstream effect*, not that a function was merely called — e.g. for an
SLA-breach AC, assert the resulting `Notification` is retrievable via `GET /api/alerts`
with the expected `type` and `recipient_id`, as shown in
`tests/alerts/test_routes.py::test_alert_created_via_event_bus_is_listed`.

## Error-path coverage

Every new `AppError` subclass raised by a sprint's change needs at least one test proving
it's reachable with the right HTTP status and `code` field — see
`tests/activities/test_routes.py::test_get_activity_not_found` and
`test_programmes/test_routes.py::test_add_unknown_user_as_member_returns_validation_error`
for the pattern.

## Coverage thresholds (case study Section 3.6 — apply regardless of stack)

| Scope | Threshold |
|---|---|
| Service layer (`app/*/service.py`) | 80% line coverage minimum |
| Route/controller layer (`app/*/routes.py`) | 70% line coverage minimum |
| Shared utilities (`app/shared/`) | 60% line coverage minimum |
| Overall project | 70% line coverage minimum |

Run: `pytest --cov=app --cov-report=term-missing` (already the default via
`pyproject.toml`'s `addopts`). The `Missing` column names exact uncovered line numbers —
use it, don't guess at what's untested.

## What NOT to do

- Don't assert on internal repository dict state directly from a route-level test — assert
  through the API (`GET` the resource back) so the test exercises the same path a real
  client would.
- Don't write a test that passes regardless of whether the business rule holds (e.g.
  asserting `resp.status_code in (200, 201, 403)` to dodge specifying the actual expected
  behavior).
- Don't skip the "not found" / "forbidden" / "validation" branches just because the "happy
  path" test passes — the Evaluator's grading-criteria checklist checks for these
  specifically.
