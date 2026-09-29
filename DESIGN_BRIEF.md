# Harness Design Brief — StoreOps Development Harness

## Section A — Intent Decomposition

**Feature decomposed**: SLA breach alerting (`PROMPT.md`) — when a `HIGH`/`CRITICAL`
task passes its due date without reaching `DONE`, notify the assigned staff member and
escalate to the store's managers if unresolved after a grace period.

### Sprint boundaries

The Planner produced a **single sprint contract**. Per `sprint-decomposition/SKILL.md`,
splitting is only warranted when a feature contains genuinely independent, separately
testable, separately valuable units of delivery — e.g. scaffolding a brand-new module
before a feature can build on it. SLA breach alerting doesn't have that shape: detection,
notification, and escalation are one coherent vertical slice through the existing
`activities` module (new `Task` fields, one new service function, one new endpoint) plus
one supporting read function in `staff`. Splitting "detection" from "escalation" into two
sprints was considered and rejected — they share the same sweep loop and the same test
setup; separating them would have meant the first sprint shipping half-working alerting
(notifications fire, but nothing ever escalates) with no independent value to a developer
reviewing it. One sprint, six acceptance criteria, stayed within
`sprint-decomposition/SKILL.md`'s 3–6 AC sizing guideline.

### Acceptance criteria structure

Every AC follows GIVEN/WHEN/THEN and names a specific, checkable outcome — not "the
feature works," but a return value, a field mutation, or a specific downstream side
effect. This is deliberate: the client's third documented failure mode was tests that
asserted HTTP status codes without verifying business rules, and a subjective AC is
exactly what produces that kind of test. Concretely, every AC in this sprint names either
a field (`sla_notified_at`, `sla_escalated_at`), a list membership (`breached`,
`escalated`), or an emitted event's payload shape (`alert_type`, `recipient_id`,
`related_entity_id`) — never a vague adjective like "correctly" or "properly."

### Example sprint contract entry, in full

> **AC4 — escalation after grace period**
> GIVEN a `Task` whose `sla_notified_at` is already set to a time more than
> `grace_period_minutes` in the past, `status != DONE`, `sla_escalated_at=None`,
> WHEN the sweep runs,
> THEN a `notification.requested` event fires with `alert_type="ESCALATION"` for every
> `STORE_MANAGER` at that store (verify via seeded user `user-1`), the task's
> `sla_escalated_at` is set, and the task's id appears in the sweep response's
> `escalated` list.
> *Architecture rule exercised: Rule 1 (module boundary — must call
> `staff.service.list_users_by_role`, never `staff.repository`).*

This AC was chosen as the example because it's the one that most directly encodes an
architecture rule into a functional requirement — the "how" (module boundary) and the
"what" (escalation fires) aren't separable in this AC, which is exactly the point: an
architecturally-sound implementation and a functionally-correct one should be the same
implementation, not two things independently checked at the end.

## Section B — Governance Framework

### Skill file strategy

| File | Scope | StoreOps-specific content |
|---|---|---|
| `app-context` | Shared | Exact module list, entity fields, seeded auth tokens, live endpoint list — not "here's how REST APIs work" |
| `architecture-principles` | Shared | The five rules, each tied to a named client failure mode and its exact check command |
| `sprint-decomposition` | Planner | Sizing guidance calibrated to *this* codebase's module count (1-2 per sprint, 3-6 ACs), with a real weak/strong AC pair from this build |
| `coding-conventions` | Generator | Actual patterns from the codebase (`Annotated[User, Depends(...)]`, the `AppError` subclass list, the `StrEnum` convention) — copy-paste-adjacent, not abstract |
| `how-to-test` | Generator | Named fixtures (`client`, `auth_header`, seeded tokens) and a real before/after example of a status-code-only test vs. a business-rule test |
| `how-to-review` | Evaluator | The exact 4-command check sequence, and the specific reasoning distinction between a read and a side effect for judging Rule 2 |
| `grading-criteria` | Evaluator | The two-dimension weighted formula, itself (see Section C) |

Shared files (`app-context`, `architecture-principles`) exist because every agent needs
the same facts about *what StoreOps is* and *what's non-negotiable about it* — duplicating
this per-agent would let one agent's copy drift from another's, silently reintroducing
inconsistency the harness exists to prevent. Role-specific files stay separate because a
Planner reading `how-to-test`'s pytest fixture details, or a Generator reading
`grading-criteria`'s scoring formula, would be pure token cost with no behavioral benefit
— see `CLAUDE.md`'s context-scoping strategy.

### The `.harness/reviews/` audit trail

Captures, per sprint: the approved `spec.md` and `sprint-N-contract.md` (what was asked
for), `sprint-N-generator-summary.md` (what was built and the Generator's own
self-assessment), `sprint-N-evaluator-feedback.md` (the independent verdict and
reasoning), and `sprint-N-run-log.md` (iteration count, token cost, quality-trend note).
Access is just repository read access — no separate permission layer, since this is
intentionally plain committed Markdown, readable by any developer or architect who can
open the repo, not a system requiring its own tooling to inspect.

**How it would surface a recurring issue**: each `run-log.md`'s quality-trend note names
which hard gate failed (if any) and which skill file looks under-specified given the
failure. If, across several future sprints, the same note kept naming
`coding-conventions` in connection with the same hard gate (say, A2 — the error-contract
gate), that's a legible, greppable signal across `.harness/reviews/sprint-*-run-log.md`
that the skill file's `AppError` example isn't landing — concrete enough to act on, unlike
a vague sense that "the AI keeps making mistakes." In this build's one demonstration
sprint, no such pattern exists yet (single PASS, no retries) — but the mechanism is what
Section 2's four failure modes call for: a recurring architectural miss should be visible
in the archive, not rediscovered by a human reviewer each time.

### One skill file rule, stated in full

From `architecture-principles/SKILL.md`, Rule 2:

> A cross-module **side effect** (not a read) must never call another module's service
> mutator directly. It must `event_bus.emit(event_name, payload)`, and the owning module
> subscribes via its own `register_event_handlers()`.

**What breaks without it**: `activities` would import and call
`app.alerts.service.create_notification(...)` directly to raise an SLA breach alert. That
compiles, passes `mypy`, and even passes the module-boundary hard gate (it's a `service`
import, not a `repository` import — Rule 1 alone wouldn't catch it). But it recreates the
client's fourth documented failure mode almost exactly: a tight, undocumented coupling
where `activities` now has to know `alerts`' internal API shape, `alerts` can't change its
notification-creation signature without an `activities` code change, and — worst — if a
third module later also needs to raise notifications, there are now two different
integration patterns in the same codebase instead of one. This is precisely why Rule 2
is scored as an LLM-assessed check rather than folded into the automated module-boundary
script: distinguishing "a legitimate read of another module's data" from "an illegitimate
direct trigger of a side effect" requires judging intent, which a grep-based import scan
cannot do — both look identical as a Python `import` statement.

## Section C — Non-Determinism Strategy

### Dimensions and weights

**Architecture Compliance — 55%**, **Functional Correctness & Test Quality — 45%**
(`grading-criteria/SKILL.md`). Architecture gets the larger weight because three of the
client's four documented failure modes (Section 2 of the case study) are architectural
— cross-module imports, raw error throws, missing event-bus integration — and only one
(status-code-only tests) is a test-quality issue. The weighting reflects where this
client's actual prior failures clustered, not a generic "structure matters more than
tests" belief — a different client context with a different failure history would
justify different weights, which is the point of grounding the weights in Section 2
rather than picking a round number.

### Hard gates, and why each cannot be a soft check

| Gate | Prevents | Why not soft |
|---|---|---|
| A1 — module boundary | Failure mode 1 (direct cross-module repository imports) | A soft/LLM check on a large diff can rate a borderline import as "probably fine" under review fatigue — exactly the ambiguity that let this failure mode reach the client's `main` the first time. A script has no fatigue and no ambiguity: an import statement either names another module's `repository` or it doesn't. |
| A2 — error contract | Failure mode 2 (raw error throws) | `ruff --select TRY002` is a byte-exact syntactic check (`raise Exception(...)` vs. a typed subclass) with zero interpretive room — making it LLM-assessed would reintroduce exactly the variability the hard-gate mechanism exists to remove, for a check that gains nothing from judgment. |
| A3 — layer separation | Structural drift enabling failure modes 1 and 4 | Same reasoning as A1 — `fastapi` either appears in a `repository.py` import list or it doesn't. |
| B1 — type checking | Silent type errors reaching runtime | `mypy --strict` either exits 0 or it doesn't; there's no partial credit for "mostly typed." |
| B2 — tests & coverage | Untested code shipping | Coverage percentages and pass/fail counts are numeric facts, not interpretations. |

Rules 2 (event-bus-only) and 5 (read-only reports) are **not** hard gates — both require
judging producer *intent* (is this a read or a side effect? is this call a write?),
which no static check can reliably resolve without false positives on legitimate reads.
Making them hard gates would either be too strict (blocking legitimate service-layer
reads that happen to touch the same module as a past violation) or too permissive (a
script pattern loose enough to avoid false positives would also miss real violations).

### Verdict-formula walkthrough

Hard gates always override the weighted score (`grading-criteria/SKILL.md` rule 1) — this
is what makes the same check results always produce the same verdict. A concrete
walkthrough, using a bug that actually occurred during this build's Generator attempt
(see `sprint-1-generator-summary.md`): `create_activity` initially didn't propagate
`payload.due_at` into the constructed `Task`, so every task's `due_at` stayed `None` and
`AC1`'s test failed with `assert 'task-1' in []`. Had this reached the Evaluator instead
of being caught by the Generator's own pre-handoff check, `pytest` would have exited
non-zero — **hard gate B2 fails** — and per the formula, the verdict is `FAIL`
immediately, without computing a weighted score at all, regardless of how clean
Dimension A's architecture compliance looked. That's the deterministic guarantee in
practice: no combination of good LLM-assessed scores can compensate for a failing test
suite, and the Evaluator never has to exercise judgment about *how badly* it failed — a
hard gate failure is binary by construction. In this build's actual run, the bug was
fixed before the Evaluator ever saw the code, so the Evaluator's real verdict was a clean
`PASS` at 100/100 (`sprint-1-evaluator-feedback.md`) — but the routing logic that would
have fired on the earlier, buggy version is the same logic, exercised the same way.

### Skill file depth vs. token budget

Every agent's context-scoping strategy (`CLAUDE.md` § Context scoping) is only affordable
because the skill files it reads are short and StoreOps-specific rather than exhaustive.
Concretely: `architecture-principles/SKILL.md` (the largest shared file) is roughly 900
tokens; a Generator attempt reads it plus `app-context`, `coding-conventions`, and
`how-to-test` — four files totaling under 4k tokens, versus the sprint contract and diff
itself, which typically dominate the actual cost (`sprint-1-run-log.md` estimates ~7.1k
total for the Generator's attempt, of which skill files are under half). This is a
deliberate trade-off, not an accident: a more exhaustive skill file — one that tried to
enumerate every edge case a rule might ever need — would cost proportionally more on
*every single invocation*, including the large majority of sprints it's irrelevant to,
in exchange for marginal benefit on the rare sprint where the extra case actually
applies. The bet is that a short, concrete file with one or two sharp examples (see
`how-to-test/SKILL.md`'s single weak/strong test pair) generalizes better per token spent
than a long file trying to be exhaustive — and that when a skill file turns out to be
under-specified for a real case, `.harness/reviews/`'s quality-trend notes are the
mechanism for catching that and growing the file precisely where it's needed, rather than
front-loading depth speculatively. This is why `monitor.agent.md` requires an estimated
token cost in every `run-log.md`: without that number recorded per sprint, a skill file
that's quietly grown too deep (and started costing more than its marginal check-quality
justifies) would be invisible until someone happened to compare invocations by hand.

### Escalation path

Triggers after 3 consecutive `FAIL` verdicts on the same sprint contract
(`CLAUDE.md` § Iteration limit and escalation). `.harness/output/escalation.md` would
contain: the sprint ID, the originating feature prompt, the iteration count (3), the
blocking issue(s) copied verbatim from the third `evaluator-feedback.md`, and every file
touched across all 3 attempts. It's surfaced directly to the developer in the same
session/channel that invoked the harness — there is no separate notification system,
consistent with this being a single-developer, single-repository tool rather than a
team-wide dashboard. This build's one demonstration sprint passed on attempt 1, so
escalation was never exercised — see `REFLECTION.md` for what that leaves untested.

## Section D — Architectural Decisions

### D1 — In-memory storage, no persistence layer

**Decision**: every module's repository is a process-lifetime `dict`, not backed by a
database. **Alternatives considered**: SQLite via SQLAlchemy (still lightweight, but
adds a migration story); a real Postgres instance in `docker-compose.yml`. **Rationale**:
the case study's own bootstrap prompt (Section 2.3) specifies "in-memory storage (no
database required)" for the baseline scaffold, and the harness's job is to govern
*application architecture* (module boundaries, error contracts, event flow), not data
persistence — adding a real database would spend build time on a concern orthogonal to
what's being demonstrated. **Assumption this depends on**: the deployed container is a
demo artifact, not a production service — data loss on container restart is acceptable
here and would not be in a real deployment, a limitation `DEPLOYMENT.md` doesn't currently
call out explicitly.

### D2 — Which architecture rules become automated hard gates vs. LLM-assessed

**Decision**: Rules 1, 3, 4 (module boundary, error contract, layer separation) are
automated, tool-backed hard gates; Rules 2, 5 (event-bus-only, read-only reports) are
LLM-assessed. **Alternatives considered**: making all five rules LLM-assessed (simpler to
build, no custom script needed — this is what the case study's own rule table (Section
3.5) shows as an *option* for some rules); or attempting to automate Rule 2 with a
heuristic script (e.g., flag any cross-module `service.py` call whose function name starts
with `create_`/`update_`/`delete_`). **Rationale**: the first three rules are syntactically
checkable with zero interpretive ambiguity (an import statement, a raise statement, a
module reference either match a pattern or they don't); Rules 2 and 5 require judging
producer intent, which is exactly what LLM review is for and what a naming-convention
heuristic would get wrong often enough to be worse than useless (a legitimate read
function named oddly, or a legitimate mutation named unconventionally, would both be
misjudged). **Assumption this depends on**: StoreOps' module boundaries stay expressible
as simple import-path and substring patterns; a future refactor introducing dynamic
imports or a plugin-style module-loading pattern would silently defeat
`scripts/check_architecture.py` without it ever failing loudly.

### D3 — Single-sprint decomposition for the demonstration feature

**Decision**: SLA breach alerting shipped as one sprint contract rather than split by
concern (e.g., "detection + notification" as sprint 1, "escalation" as sprint 2).
**Alternatives considered**: the two-sprint split above; a three-way split separating the
new `staff.service.list_users_by_role` read function into its own sprint. **Rationale**:
per `sprint-decomposition/SKILL.md`, a split is only justified when each half is
independently valuable and independently testable — detection-without-escalation is not
a feature a developer would want merged on its own (it's half of what was asked for), and
the `staff` read function has no standalone use case outside this sprint. Splitting would
have added coordination overhead (two `sprint-N-contract.md` files, two Generator/Evaluator
cycles) without a corresponding benefit. **Assumption this depends on**: a single Generator
attempt can hold the whole slice's context without degrading — true for a
6-AC, 2-module change at this codebase's current size, but this assumption is exactly
what would break first if StoreOps grew significantly larger, at which point
`sprint-decomposition/SKILL.md`'s "don't split just to make sprints smaller" guidance
would need revisiting.
