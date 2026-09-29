# Skill: Architecture Principles

Shared foundation skill — read by every agent before acting. These are the five
non-negotiable StoreOps architecture rules (case study Section 3.5). Each one exists
because of a specific failure the client's standards team observed in a prior AI-assisted
experiment (case study Section 2). Cite the rule by name in sprint contracts and
evaluator feedback — never restate it generically.

## Rule 1 — Module boundary

**Prevents client failure mode 1**: "Direct imports from another module's repository,
bypassing the agreed service boundary and event bus."

No module may import `app.<other_module>.repository` directly. A cross-module **read**
goes through the target module's `service.py` only — e.g. `app/activities/service.py`
calling `app.staff.service.get_user_by_id(...)` and `app.programmes.service.get_programme(...)`
is correct; importing `app.staff.repository` or `app.programmes.repository` from
`app/activities/` is a violation.

**Automated check** (hard gate): `python scripts/check_architecture.py` —
`check_module_boundary()` scans every `.py` file under `app/` for
`from app.<module>.repository import` and flags any match where the importing file's own
module differs from `<module>`.

## Rule 2 — Event bus only

**Prevents client failure mode 4**: "Missing event bus integration — state changes
written directly to sibling module repositories."

A cross-module **side effect** (not a read) must never call another module's service
mutator directly. It must `app.shared.event_bus.event_bus.emit(event_name, payload)`, and
the owning module subscribes via its own `register_event_handlers()` (see
`app/alerts/service.py` for the existing pattern: it subscribes to
`"notification.requested"`). Example: a future SLA-breach sweep in `activities` must emit
`event_bus.emit("notification.requested", {...})`, not call
`app.alerts.service.create_notification(...)` itself.

**Check** (LLM-assessed): the Evaluator inspects the diff for any new cross-module call
that mutates state outside the calling module's own repository, and confirms it goes
through `event_bus.emit(...)` rather than a direct service-mutator call.

## Rule 3 — Error contract

**Prevents client failure mode 2**: "Raw Error throws in service methods, bypassing the
project's typed AppError hierarchy."

Every error raised from `app/*/service.py` or `app/*/routes.py` must be a subclass of
`app.shared.errors.AppError` (`NotFoundError`, `ValidationError`, `ForbiddenError`,
`ConflictError`, `UnauthorizedError`, or a new subclass added to `shared/errors.py` if none
fits — never a bare `Exception`, `ValueError`, `KeyError`, etc.).

**Automated check** (hard gate): `ruff check --select TRY002` — the `tryceratops` rule
flags any `raise Exception(...)` or other vanilla-exception raise. Verified working: see
`DESIGN_BRIEF.md` Section C for the walkthrough.

## Rule 4 — Layer separation

**Prevents structural drift underlying failure modes 1 and 4**: keeping Routes → Service
→ Repository strictly one-directional is what makes Rules 1 and 2 enforceable at all.

- `routes.py`: HTTP concerns and request/response validation only. No business logic, no
  direct repository import (must go through its own module's `service.py`).
- `service.py`: business logic, typed errors, cross-module reads via other modules'
  `service.py`, cross-module side effects via `event_bus.emit`.
- `repository.py`: data access only. Must never import `fastapi` or contain HTTP concerns.

**Automated check** (hard gate): `python scripts/check_architecture.py` —
`check_layer_separation()` flags any `repository.py` importing `fastapi`, and any
`routes.py` importing its own module's `repository.py` directly.

## Rule 5 — Read-only reports

**Applies once the `reports` module exists** (it does not yet — see `app-context/SKILL.md`).
`reports` aggregates data from `activities`, `programmes`, and `staff` for summaries and
rollups, but must never write to those modules — no calls to their `create_*`/`update_*`/
`delete_*` service functions, ever, in either direction.

**Check** (LLM-assessed, once applicable): the Evaluator confirms no write call from
`app/reports/*` into another module's service layer.

## How these map to Evaluator hard gates

See `.harness/skills/grading-criteria/SKILL.md` — Rules 1, 3, and 4 each back a hard,
automated gate; Rules 2 and 5 are LLM-assessed because they require judging intent (is this
call a read or a side effect?) that a grep-based script cannot reliably distinguish.
