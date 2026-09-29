# CLAUDE.md — StoreOps Harness Orchestrator

This file is read automatically by Claude Code when invoked in this repository. It is the
**orchestration brain**: it defines how a feature request becomes governed, tested,
production-ready code. It does not contain StoreOps business rules or coding standards —
those live in `.harness/skills/` and are read by the agents below, not by this file.

## Entry prompt format

A developer starts a harness run with a single message:

```
@planner <feature description>
```

Example: `@planner Add SLA breach alerting: when a HIGH or CRITICAL task passes its due
date without reaching DONE, automatically fire an SLA_BREACH notification to the assigned
Department Lead and escalate to STORE_MANAGER if unresolved after a configurable grace
period.`

One feature per invocation. The Planner is the only valid entry point — never invoke the
Generator or Evaluator directly; they are reached only through the loop below.

## Agent roster

| Agent | File | Invoked by | Reads (minimum) | Produces |
|---|---|---|---|---|
| Planner | `.harness/agents/planner.agent.md` | Developer's `@planner` prompt | `app-context`, `architecture-principles`, `sprint-decomposition` skills | `.harness/output/spec.md`, `.harness/output/sprint-N-contract.md` |
| Generator | `.harness/agents/generator.agent.md` | Orchestrator, after `APPROVED` or after a FAIL retry | `app-context`, `architecture-principles`, `coding-conventions`, `how-to-test`, `api-integration` skills | Code in `src` (`app/`), `.harness/output/generator-summary.md` |
| Evaluator | `.harness/agents/evaluator.agent.md` | Orchestrator, after every Generator run | `architecture-principles`, `how-to-review`, `grading-criteria` skills | `.harness/output/evaluator-feedback.md` |
| Monitor | `.harness/agents/monitor.agent.md` | Orchestrator, after every Evaluator verdict | The completed sprint's `evaluator-feedback.md` + `generator-summary.md` | `.harness/reviews/sprint-N-run-log.md`, plus archived copies of `sprint-N-evaluator-feedback.md` and `sprint-N-generator-summary.md` |

## Orchestration sequence

1. Developer sends `@planner <feature>`.
2. Planner decomposes the feature into one or more sprint contracts and writes
   `.harness/output/spec.md`, ending with a literal `STATUS: AWAITING APPROVAL` marker.
3. Orchestrator halts and surfaces `spec.md` to the developer. No further action happens
   until the developer replies with exactly `APPROVED`. (If the developer instead replies
   with changes, Planner revises `spec.md` and the AWAITING APPROVAL marker is re-emitted.)
4. On `APPROVED`, for each sprint contract in order:
   a. Invoke Generator with that sprint's contract → produces code + `generator-summary.md`.
   b. Invoke Evaluator with `generator-summary.md` and the diff it describes → produces
      `evaluator-feedback.md` with a `VERDICT:` line of `PASS`, `CONDITIONAL PASS`, or `FAIL`.
   c. Invoke Monitor → archives `sprint-N-run-log.md` to `.harness/reviews/`.
   d. Apply the routing logic below.
5. When every sprint contract has reached PASS or CONDITIONAL PASS, the orchestrator reports
   completion to the developer with a summary of files changed, tests added, and any
   "known gaps" carried from CONDITIONAL PASS verdicts. The run ends — the developer is not
   re-prompted per sprint; steps a–d repeat autonomously without manual triggering.

## Routing logic

The orchestrator reads the `VERDICT:` line of the current sprint's `evaluator-feedback.md`
and decides the next action deterministically:

- **PASS** → Monitor archives the run; advance to the next sprint contract (or finish, if
  this was the last one).
- **CONDITIONAL PASS** → treat as PASS for progression purposes, but carry the Evaluator's
  noted follow-ups into the final completion summary as "known gaps" for the developer to
  triage later; advance to the next sprint contract.
- **FAIL** → increment this sprint's iteration counter; feed `evaluator-feedback.md`
  verbatim back to the Generator as its correction brief; the Generator revises only the
  files `evaluator-feedback.md` flags (not a full rewrite); Evaluator re-runs against the
  revised diff.

The iteration counter is per sprint contract and resets to 0 when a new sprint contract
begins.

## Iteration limit and escalation

Maximum **3** Generator attempts per sprint contract. If the verdict is still `FAIL` after
the 3rd attempt:

1. The orchestrator halts the loop for that sprint contract — it does not proceed to any
   later sprint contracts in this run.
2. The orchestrator writes `.harness/output/escalation.md` containing: the sprint ID, the
   originating feature prompt, the iteration count (3), the blocking issue(s) copied
   verbatim from the final `evaluator-feedback.md`, and the list of files touched across all
   3 attempts.
3. The orchestrator reports to the developer that escalation occurred, and where to find the
   notice. Resolution is manual from here: the developer edits code directly, adjusts the
   sprint contract, or overrides the Evaluator's finding with a documented reason. Once
   resolved, the developer resumes with `@generator retry sprint-N`.

## Context scoping strategy

Each agent invocation starts from a bounded, fresh context — the orchestrator does not carry
a prior agent's full reasoning forward, only the handoff files under `.harness/output/`. This
is deliberate: it caps token cost per invocation and prevents context-window degradation
across a long, multi-sprint, multi-retry run. Concretely:

- **Planner** reads only its skill files and the developer's prompt.
- **Generator** reads only its skill files, the current sprint contract, and — on a retry —
  the latest `evaluator-feedback.md`. It never re-reads prior sprints' contracts or diffs.
- **Evaluator** reads only its skill files, the current sprint contract, the current
  `generator-summary.md`, and a diff of files changed this sprint. It never reads the full
  repository history.
- **Monitor** reads only the current sprint's `evaluator-feedback.md` and
  `generator-summary.md`.

This trades some completeness (an agent cannot reference decisions made in earlier sprints
except through what the contract or skill files restate) for staying reliably within each
agent's effective context budget across up to 3 Generator retries per sprint. Skill files are
kept short and StoreOps-specific rather than exhaustive for the same reason — see
`DESIGN_BRIEF.md` Section C for the token-cost trade-off this strategy accepts.

## CI/CD relationship

`.harness/` is deliberately kept separate from `.github/` (or any CI configuration) — see
Repository Structure below. The Evaluator's automated checks — `mypy .`, `ruff check .`, and
`pytest --cov=app --cov-report=term-missing` — are the **same commands** a CI pipeline would
run, but the harness runs them **before** commit, inside the agent loop, as a pre-merge gate.
The harness does not replace CI: CI still runs independently on every push/PR as the final
gate. The harness's purpose is to make a CI failure rare, by catching the four StoreOps
failure modes documented in Section 2 of the case study (cross-module imports, raw error
throws, tests that don't verify business rules, missing event-bus integration) at generation
time rather than at review time. If this repository later adds a CI pipeline, it should run
the identical check commands so a harness PASS and a CI PASS never disagree.

## Monitor and the reviews archive

After every sprint's Evaluator verdict, Monitor archives that sprint's
`evaluator-feedback.md` and `generator-summary.md` from `.harness/output/` into
`.harness/reviews/` (renamed with the `sprint-N-` prefix), and writes
`.harness/reviews/sprint-N-run-log.md`, recording: sprint ID, verdict, iterations used,
escalation flag (yes/no), an estimated token cost for the sprint, and one line of
quality-trend notes (e.g. "hard gate `error-contract` failed on attempt 1 — raw
`ValueError` in `programmes/service.py`; passed on retry — consider strengthening the
`coding-conventions` skill's error-handling example"). This archive is permanent — committed,
never gitignored — and is the primary observability input for deciding which skill files need
refinement over time.

## Repository structure

| Path | Purpose |
|---|---|
| `CLAUDE.md` | This file — orchestrator |
| `PROMPT.md` | The feature prompt used for the demonstration run |
| `REFLECTION.md` | Post-run reflection (max 1 page) |
| `DESIGN_BRIEF.md` | Harness Design Brief (3–5 pages) |
| `JOURNAL.md` | Architecture journal, kept throughout the build |
| `.harness/agents/` | `planner.agent.md`, `generator.agent.md`, `evaluator.agent.md`, `monitor.agent.md` |
| `.harness/skills/` | All skill files, one named subdirectory per skill (e.g. `app-context/SKILL.md`) |
| `.harness/output/` | Working files for the run in progress: `spec.md`, `sprint-N-contract.md`, `generator-summary.md`, `evaluator-feedback.md`, `escalation.md`. Gitignored — ephemeral. |
| `.harness/reviews/` | Archived, permanent record per sprint: `sprint-N-evaluator-feedback.md`, `sprint-N-generator-summary.md`, `sprint-N-run-log.md`. Committed — the governance audit trail. |
| `app/` | StoreOps source code (`activities/`, `programmes/`, `staff/`, `alerts/`, `shared/`; `reports/` added by a future harness run) |
| `tests/` | Test files, mirroring `app/`'s module structure |
