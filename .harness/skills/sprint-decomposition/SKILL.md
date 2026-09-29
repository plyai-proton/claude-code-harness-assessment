# Skill: Sprint Decomposition

Planner-specific skill. How to turn one feature prompt into sprint contracts the
Generator can implement in a single bounded pass.

## Default: one sprint

Most StoreOps features are a single vertical slice through the existing three-layer
architecture (routes → service → repository, one or two modules) plus tests. Default to
**one** sprint contract. Only split into multiple sprints when the feature contains
genuinely independent units of delivery, e.g.:

- Scaffolding a brand-new module (like `reports`) is a different sprint from wiring a
  feature that depends on it — the module needs to exist and pass its own checks before a
  feature can safely build on it.
- A feature with a clearly separable "make the data available" step and "act on the data"
  step (e.g. sprint 1: emit the domain event; sprint 2: a second module reacts to it) — but
  only split this way if each half is independently testable and independently valuable;
  do not split just to make sprints smaller.

Do not split a feature into more than 3 sprints. If it looks like it needs more, the
feature prompt is probably too large for one harness run — flag this in `spec.md` under
assumptions rather than forcing an artificial decomposition.

## Sizing a sprint

A well-sized sprint contract:
- Touches 1–2 modules.
- Has 3–6 acceptance criteria — fewer suggests the sprint is trivial and could be merged
  with adjacent work; more suggests it should split.
- Is implementable and independently testable within one Generator attempt without the
  Generator needing to guess at a later sprint's contents.

## GIVEN/WHEN/THEN format

Each acceptance criterion must be independently testable by an automated test — never a
vague outcome statement. Structure:

```
GIVEN <preconditions: entity state, role, request shape>
WHEN <the action under test>
THEN <the observable, assertable outcome — a return value, a status code AND a business
      state change, an emitted event, a persisted field>
```

**Weak** (rejected — not independently testable, no business-rule assertion):
> The SLA breach feature works correctly.

**Strong** (StoreOps example, from the reference SLA-breach-alerting feature):
> GIVEN a `Task` with `priority=CRITICAL`, `status != DONE`, and `due_at` in the past,
> WHEN the SLA sweep runs,
> THEN `event_bus.emit("notification.requested", ...)` is called with `alert_type=SLA_BREACH`,
> `recipient_id` equal to the task's `assignee_id`, and the resulting `Notification` is
> retrievable via `GET /api/alerts` for that recipient.

This is strong specifically because it names the exact event, the exact payload field to
check, and a second, independent way to verify the outcome (the alerts endpoint) — a test
against it cannot pass by accident, and it directly avoids client failure mode 3 ("tests
that asserted HTTP status codes but did not verify business rule compliance").

## Naming which architecture-principles rules apply

For each sprint, name only the rules the sprint actually exercises (see
`architecture-principles/SKILL.md`) — never all five by default:

- New endpoint touching only its own module's three layers → Rule 4 (layer separation) and
  Rule 3 (error contract) apply; Rules 1 and 2 usually don't unless it reads or triggers
  something outside its own module.
- Feature needs data owned by another module → Rule 1 (module boundary) applies; the
  Generator must call that module's `service.py`, never its `repository.py`.
- Feature creates a side effect visible to another module (e.g. a notification, a
  downstream report) → Rule 2 (event bus only) applies.
- Feature touches `reports` → Rule 5 (read-only reports) applies.

## Sprint ID and file naming

Sprint contracts are numbered `sprint-1`, `sprint-2`, ... in delivery order, written to
`.harness/output/sprint-N-contract.md`. `spec.md` lists them in the same order with each
sprint's one-line goal, so the developer can approve the whole plan in one read.
