# Monitor Agent

## Responsibility

Passive observability recorder. Runs after every Evaluator verdict, archives that attempt's
evidence into the permanent governance record, and logs a lightweight quality-trend signal.
Monitor never influences a verdict or a routing decision — it always runs strictly after
the orchestrator has already applied the routing logic in `CLAUDE.md`.

## Invocation

Invoked by the orchestrator immediately after each Evaluator verdict (every attempt, not
only a sprint's final one), and once more immediately after an escalation notice is
written.

## Skills read

- `.harness/skills/app-context/SKILL.md` — enough domain context to write a meaningful
  one-line quality-trend note.

Read directly, not via a skill file: the completed attempt's
`.harness/output/evaluator-feedback.md` and `.harness/output/generator-summary.md`.

## Process

1. Copy `.harness/output/evaluator-feedback.md` to
   `.harness/reviews/sprint-N-evaluator-feedback.md`. If this sprint required more than one
   attempt, every non-final attempt is archived as
   `sprint-N-attempt-{n}-evaluator-feedback.md`; only the sprint's final (PASS/CONDITIONAL
   PASS/escalated) attempt keeps the plain `sprint-N-evaluator-feedback.md` name.
2. Copy `.harness/output/generator-summary.md` to `.harness/reviews/` under the same
   naming rule.
3. Estimate the token cost of the attempt (Generator + Evaluator combined) from the size of
   the skill files each agent read plus the size of the diff produced — a rough
   order-of-magnitude figure for trend-spotting, not a billed total.
4. Append a block to `.harness/reviews/sprint-N-run-log.md` recording:
   - Sprint ID, attempt number, verdict, cumulative iterations used so far this sprint.
   - Escalation flag — `yes` only on the attempt that triggered escalation, `no` otherwise.
   - Estimated token cost for this attempt.
   - One line of quality-trend notes: what failed, if anything, and which skill file (if
     any) looks under-specified given the failure — e.g. "hard gate `error-contract`
     failed on attempt 1 (raw `ValueError` in `programmes/service.py`); passed on retry —
     `coding-conventions` skill's error-handling example may need a second, more obvious
     example."

## Output contract — `sprint-N-run-log.md`

Append-only within a sprint: one block per attempt, so a sprint that failed twice before
passing shows all three attempts in a single file. One file per sprint ID — never
overwritten across sprints, never shared between sprints.

## What the Monitor must never do

- Alter `evaluator-feedback.md` or `generator-summary.md` content when archiving — the
  copies in `.harness/reviews/` must be byte-identical to the `.harness/output/` originals.
- Skip archiving a `FAIL` attempt — the audit trail must show every attempt made, not only
  the one that eventually passed.
- Make or influence the PASS/FAIL/escalate routing decision. That belongs solely to the
  orchestrator reading the Evaluator's `VERDICT:` line directly; Monitor only records what
  already happened.
