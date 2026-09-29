# Sprint 1 Contract — SLA Breach Alerting

## Goal

Implement a triggerable SLA-breach sweep for `activities` that notifies the assigned
staff member on breach and escalates to the store's `STORE_MANAGER`s if unresolved after
a grace period, idempotently.

## Files expected to change

- `app/activities/models.py` — add `due_at`, `sla_notified_at`, `sla_escalated_at` to
  `Task`; add `due_at` to `TaskCreate`; add a `SlaSweepResult` response model.
- `app/activities/service.py` — add `run_sla_breach_sweep(store_id, *, grace_period_minutes)`.
- `app/activities/routes.py` — add `POST /api/activities/sla-sweep`.
- `app/staff/repository.py` — add `list_by_store_and_role(store_id, role)`.
- `app/staff/service.py` — add `list_users_by_role(store_id, role)` (the module-boundary-
  respecting read interface `activities.service` must use).
- `tests/activities/test_sla_sweep.py` — new test file covering all acceptance criteria
  below.

## Acceptance criteria

**AC1 — breach detected and notified**
GIVEN a `Task` with `priority=CRITICAL`, `status=TODO`, `due_at` in the past, and
`sla_notified_at=None`,
WHEN `POST /api/activities/sla-sweep` runs for that store,
THEN a `notification.requested` event fires with `alert_type="SLA_BREACH"`,
`recipient_id` equal to the task's `assignee_id`, and the resulting `Notification` is
retrievable via `GET /api/alerts` for that recipient; the task's `sla_notified_at` is set;
the task's `id` appears in the sweep response's `breached` list.
*Architecture rules exercised: Rule 2 (event-bus-only), Rule 3 (error contract, for
invalid input — see AC6), Rule 4 (layer separation).*

**AC2 — priority filter honored**
GIVEN a `Task` with `priority=LOW` (or `MEDIUM`), `status != DONE`, `due_at` in the past,
WHEN the sweep runs,
THEN no notification is emitted for that task and its id appears in neither the
`breached` nor `escalated` list.

**AC3 — completed tasks never breach**
GIVEN a `Task` with `priority=HIGH`, `status=DONE`, `due_at` in the past,
WHEN the sweep runs,
THEN no notification is emitted for that task.

**AC4 — escalation after grace period**
GIVEN a `Task` whose `sla_notified_at` is already set to a time more than
`grace_period_minutes` in the past, `status != DONE`, `sla_escalated_at=None`,
WHEN the sweep runs,
THEN a `notification.requested` event fires with `alert_type="ESCALATION"` for every
`STORE_MANAGER` at that store (verify via seeded user `user-1`), the task's
`sla_escalated_at` is set, and the task's id appears in the sweep response's `escalated`
list.
*Architecture rule exercised: Rule 1 (module boundary — must call
`staff.service.list_users_by_role`, never `staff.repository`).*

**AC5 — grace period honored**
GIVEN a `Task` whose `sla_notified_at` is set to a time less than `grace_period_minutes`
in the past,
WHEN the sweep runs,
THEN no escalation notification is emitted yet.

**AC6 — idempotent re-run and input validation**
GIVEN a `Task` that already has `sla_escalated_at` set,
WHEN the sweep runs again,
THEN no duplicate `SLA_BREACH` or `ESCALATION` notification is emitted for that task.
ADDITIONALLY, GIVEN `grace_period_minutes=0` (or negative) is passed to the sweep
endpoint, WHEN the sweep runs, THEN a `ValidationError` (HTTP 422, `code:
"VALIDATION_ERROR"`) is raised — not a raw exception.

## Out of scope for this sprint

- Wiring an actual scheduler/cron to call the sweep automatically (see `spec.md`
  Assumption 1).
- A `reports` view of SLA breach history.
- Per-store configurable grace period storage (the parameter is caller-supplied only).
