# Architecture Journal

Kept across the build. Captures trade-offs and decisions as they were made, including
ones that didn't make it into `DESIGN_BRIEF.md`'s four formal decisions — this is the more
informal, chronological record; the Brief is the polished argument for the choices that
mattered most.

## Phase: Planning and stack choice

Picked Python/FastAPI over Node.js despite the case study noting Node has "the most
detailed reference implementation." Traded a slightly less-trodden path in the
programme's own materials for a stack where I could write more idiomatic, opinionated
code faster — which matters more for skill-file credibility than following the
best-documented option, since `sprint-decomposition/SKILL.md`'s own guidance is "choose
the stack you know best... a superficial skill file written in an unfamiliar language
will score poorly."

Deployment target: local Docker over cloud, chosen for reproducibility without cloud
credentials or cost, at the cost of the AI Platform Services competency's cloud-specific
credit. Revisit if time allows — right now `DEPLOYMENT.md` documents the trade-off but
doesn't hedge against it.

## Phase: Scaffold generation

Deliberately built `staff` as auth-only — no `routes.py` at all — following the case
study's Section 3.6 note that staff has "no CRUD surface here." This turned out to matter
more than expected once the SLA-alerting sprint needed a `staff` read function: it forced
the new `list_users_by_role` function to live in `staff.service` (the only interface
`staff` exposes) rather than tempting a shortcut through a hypothetical staff endpoint.
Good accidental validation that the module's shape was right from the start.

Renamed `ActivityRepository.list` and `ProgrammeRepository.list` to `list_by_store`
during baseline generation — not a style preference, `mypy --strict` genuinely failed
(`"list" is not valid as a type`) because a method named `list` shadows the builtin
within its own class body once a later method's return annotation tries to use
`list[X]`. Small thing, but it's the kind of failure that's invisible until `mypy` is
actually run — exactly why the harness's hard gates run real tools rather than trusting
a self-report.

## Phase: Orchestrator and agents

The hardest design call in `CLAUDE.md` was the context-scoping section — how much should
each agent be allowed to remember from prior sprints or prior attempts? Landed on "almost
nothing beyond the handoff files" specifically because the retry path (up to 3 Generator
attempts) is where context bloat would compound fastest: if attempt 2's Generator carried
forward all of attempt 1's reasoning plus the new feedback, by attempt 3 the prompt would
be dominated by stale context rather than the actual correction needed. Decided a retry
reads only `evaluator-feedback.md`, not the original sprint contract — a bet that
well-written Evaluator feedback names everything needed without re-deriving the whole
sprint from scratch.

## Phase: Skill files and hard gates

Original plan was to make all five architecture rules LLM-assessed, matching the case
study's own rule table which lists some as "LLM-assessed" without requiring automation.
Changed my mind partway through writing `architecture-principles/SKILL.md` once it became
clear that Rules 1, 3, and 4 are just import/pattern checks with no ambiguity — building
`scripts/check_architecture.py` took maybe 20 minutes and turned three "hopefully the
Evaluator remembers to check this" items into three "this is a fact, not a judgment"
items. Worth the build time; see `DESIGN_BRIEF.md` Section D2 for the fuller argument.
Tested the script and `ruff --select TRY002` against deliberately injected violations
before trusting them as gates — a hard gate that's never been seen to actually fail isn't
verified, it's just hoped.

## Phase: Demonstration run

Chose SLA breach alerting over the other three suggested features (bulk handover,
regional rollup, planogram template) specifically because it's the only one of the four
that exercises both a cross-module read (Rule 1) and a cross-module side effect (Rule 2)
in the same feature — the richest single test of the harness's actual governance
surface. Regional rollup would have required building the `reports` module from scratch
first, which felt like it would shift the demonstration's weight toward "did a new module
get scaffolded correctly" rather than "did the harness govern a realistic feature."

The `due_at` propagation bug (see `REFLECTION.md`) was a genuine miss, not planted for
effect — worth recording that the first version of `create_activity`'s edit looked
correct on read-through and only failed because `AC1`'s test asserted the specific
downstream consequence (task appearing in `breached`) rather than just that the sweep
endpoint returned 200. Direct, lived evidence for why `how-to-test/SKILL.md`'s
"business rules, not status codes" rule exists.

## Phase: Deployment and write-up

`docker compose ps` showing `healthy` wasn't enough on its own to trust — the healthcheck
only proves `/health` responds, not that the harness-added feature works inside the
container. Re-ran the full create → sweep → alert sequence against the containerized
app specifically because "the container starts" and "the feature works in the container"
are different claims, and only the second one is what `DEPLOYMENT.md` actually needs to
support.
