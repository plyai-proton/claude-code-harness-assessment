# Generator Summary — sprint-1, attempt 1

## AC self-check table

| AC | Description | Self-check | Proving test |
|---|---|---|---|
| AC1 | Breach detected and notified | PASS | `test_sla_sweep.py::test_ac1_breach_detected_and_notified` |
| AC2 | Priority filter honored | PASS | `test_sla_sweep.py::test_ac2_priority_filter_honored` |
| AC3 | Completed tasks never breach | PASS | `test_sla_sweep.py::test_ac3_done_tasks_never_breach` |
| AC4 | Escalation after grace period | PASS | `test_sla_sweep.py::test_ac4_escalation_after_grace_period` |
| AC5 | Grace period honored | PASS | `test_sla_sweep.py::test_ac5_grace_period_honored` |
| AC6a | Idempotent re-run | PASS | `test_sla_sweep.py::test_ac6_idempotent_rerun_after_escalation` |
| AC6b | Invalid grace period raises ValidationError | PASS | `test_sla_sweep.py::test_ac6_invalid_grace_period_raises_validation_error` |

## Files changed

| File | Layer | Change |
|---|---|---|
| `app/activities/models.py` | models | Added `due_at`, `sla_notified_at`, `sla_escalated_at` to `Task`; `due_at` to `TaskCreate`; new `SlaSweepResult` model |
| `app/activities/service.py` | service | Added `run_sla_breach_sweep`; fixed `create_activity` to propagate `due_at` from payload into the constructed `Task` (caught by self-check, see below) |
| `app/activities/routes.py` | routes | Added `POST /api/activities/sla-sweep` |
| `app/staff/repository.py` | repository | Added `list_by_store_and_role` |
| `app/staff/service.py` | service | Added `list_users_by_role` — the module-boundary-respecting read interface `activities.service` calls for escalation recipients |
| `tests/activities/test_sla_sweep.py` | test | New — covers AC1–AC6b |
| `tests/conftest.py` | test infra | Added autouse `_reset_module_state` fixture resetting `activity_repository`, `alert_repository`, `programme_repository` between tests (see Known gaps / self-correction below) |
| `tests/activities/test_service.py` | test | Removed now-redundant local reset fixture, superseded by `conftest.py`'s |

## Self-corrections made during self-check (before handoff)

Per `generator.agent.md`: "Run the automated checks locally... Fix failures before
proceeding — do not hand off code that fails its own checks." Two issues were found and
fixed during this step, not left for the Evaluator:

1. **`due_at` not propagated.** `TaskCreate.due_at` was added to the model but
   `create_activity` still constructed `Task(...)` without passing it through, so every
   created task's `due_at` silently stayed `None` and no task could ever breach. Caught by
   AC1's test failing (`assert 'task-1' in []`). Fixed by adding `due_at=payload.due_at` to
   the constructor call in `app/activities/service.py`.
2. **Cross-test-file state leak.** `alert_repository` and `programme_repository` are
   process-wide singletons with no reset between tests (only `activity_repository` had a
   local reset fixture, in `test_service.py`). Once `test_sla_sweep.py` started creating
   real notifications, `tests/alerts/test_routes.py::test_list_alerts_empty_by_default`
   started failing — a pre-existing test-isolation gap the new sprint's tests exposed
   rather than caused. Fixed by centralizing repository resets in a `conftest.py` autouse
   fixture rather than patching the one failing test, and removed the now-redundant local
   fixture in `test_service.py`.

## Known gaps

- No real scheduler triggers the sweep automatically — it's a manually-triggerable
  endpoint (`spec.md` Assumption 1). Wiring a scheduler is out of scope for this sprint.
- Grace period is caller-supplied per request, not a persisted per-store setting
  (`spec.md` Assumption 3).
- "Assigned staff member" was used in place of the case study's "assigned Department
  Lead" wording, since `Task` has no department-lead reference (`spec.md` Assumption 2).
  This is a deliberate scope narrowing, not an oversight — flagged for developer review.

## Automated check results

```
mypy .                                          → Success: no issues found in 26 source files
ruff check .                                    → All checks passed
python scripts/check_architecture.py            → 0 violations
pytest --cov=app --cov-report=term-missing      → 19 passed, 97% overall coverage
  app/activities/service.py: 92% (≥80% threshold)
  app/activities/routes.py: 100% (≥70% threshold)
  app/shared/*: 92–100% (≥60% threshold)
```
