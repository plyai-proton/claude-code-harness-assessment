# Spec — SLA Breach Alerting

**Source**: `PROMPT.md` (the `@planner` message that invoked this harness run).

## Feature summary

When a `HIGH` or `CRITICAL` priority `Task` passes its due date without reaching `DONE`,
the system must notify the assigned staff member, and escalate to the store's managers if
the breach remains unresolved after a configurable grace period.

## Modules touched

- `activities` — owns the breach-detection logic and the new trigger endpoint; gains new
  `Task` fields to track breach/escalation state.
- `staff` — gains a read-only lookup (`list_users_by_role`) so `activities` can find a
  store's `STORE_MANAGER`s without importing `staff.repository` (Rule 1).
- `alerts` — unchanged. Already subscribes to `notification.requested`; this feature is a
  new *producer* of that event, not a change to the consumer.

## Sprint contracts

- **sprint-1**: Implement SLA breach detection, notification, and escalation as a
  triggerable sweep over one store's activities, with idempotent re-runs. Single sprint —
  this is one coherent vertical slice (new `Task` fields, one new service function, one new
  endpoint, one new `staff.service` read function, tests) and does not warrant splitting
  per `sprint-decomposition/SKILL.md`.

## Assumptions (ambiguity resolved by the Planner)

1. **No scheduler exists in this codebase.** The case study describes this as something
   that happens automatically, but StoreOps has no background job runner. This sprint
   implements the breach check as a **triggerable sweep** (`POST
   /api/activities/sla-sweep`) rather than a real cron/background task — wiring an actual
   scheduler is out of scope for this demonstration and would be its own sprint if needed
   later. In production this endpoint would be called by an external scheduler.
2. **"Assigned staff member"**, not literally "the assigned Department Lead" as the
   original case-study wording suggests: `Task` has no direct "department lead" reference
   — only `assignee_id` (any staff member) and `owner_id`. The Planner narrowed the prompt
   wording to "the assigned staff member" (falling back to the task's owner if
   unassigned) rather than inventing a department-lead-lookup concept the domain model
   doesn't currently support. This is stated explicitly here, not silently substituted.
3. **Grace period** is a caller-supplied parameter on the sweep endpoint
   (`grace_period_minutes`, default 60), not a stored per-task or per-store setting — no
   such setting exists yet and the prompt says "configurable," which a request parameter
   satisfies without inventing new persistent configuration state.
4. **Idempotency**: re-running the sweep must not re-notify or re-escalate a task already
   handled. This wasn't explicit in the prompt but is necessary for the endpoint to be
   safely callable on a recurring basis (its intended real-world use), so it's included as
   an acceptance criterion.

## Sprint contract list

| Sprint | Goal |
|---|---|
| sprint-1 | SLA breach detection, notification, and manager escalation via a triggerable sweep endpoint |

STATUS: AWAITING APPROVAL
