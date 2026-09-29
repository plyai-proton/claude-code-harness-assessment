# Reflection

## What the harness did well

The Generator's mandatory self-check step (`generator.agent.md`: "run the automated
checks... fix failures before handing off") caught two real defects before the Evaluator
ever saw the code: a missing `due_at` field propagation in `create_activity`, and a
pre-existing cross-test-file state leak in `alert_repository`/`programme_repository` that
this sprint's new tests happened to expose. Neither was a contrived example — both broke
real tests (`AC1` failed with `assert 'task-1' in []`; `test_list_alerts_empty_by_default`
failed once alerts started persisting across files). That the process caught and fixed
both without needing an Evaluator `FAIL`/retry cycle is a good sign the skill files
(`coding-conventions`, `how-to-test`) carry enough concrete, StoreOps-specific detail to
be actionable, not just aspirational. The hard gates also held up under a deliberate
stress test: `scripts/check_architecture.py` correctly flagged an injected cross-module
repository import with an exact `path:line`, and `ruff --select TRY002` correctly flagged
a raw `raise Exception(...)` — both verified working before being trusted as gates, not
assumed to work from the skill file text alone.

## Where it fell short

The most significant limitation is one the Design Brief's Section C walkthrough already
hints at: this demonstration ran Planner, Generator, and Evaluator as sequential steps
within **one continuous session**, not as genuinely separate invocations with the bounded,
fresh context `CLAUDE.md`'s context-scoping strategy describes. That means the Evaluator
reviewing sprint-1's code had full memory of having written it — a much easier position
than a real fresh Evaluator invocation that only sees `generator-summary.md` and a diff,
the way `evaluator.agent.md` specifies. The verdict this run produced (PASS, 100/100) is
real and the checks behind it are real, but it doesn't prove the skill files alone are
sufficient to get a *genuinely independent* review to the same conclusion — which is the
harder and more useful thing to demonstrate. Separately, `CLAUDE.md`'s developer-approval
gate (`spec.md` ending in `AWAITING APPROVAL`, halting until the developer types
`APPROVED`) was treated as satisfied by the user's prior instruction to continue the
demonstration run, rather than a literal approval message — a reasonable shortcut for a
single guided session, but not a faithful test of the gate as designed. The 3-attempt
escalation path was also never exercised, since sprint-1 passed on attempt 1 — the
`escalation.md` format is specified and documented but unverified in practice.

## One concrete improvement

Re-run this same demonstration feature using the `Agent` tool to dispatch the Generator
and Evaluator as actual separate subagent invocations — each given only the files its
`agent.md` says it reads (its skill files plus the current sprint contract or
generator-summary), with no access to the orchestrating session's own reasoning about how
the code was written. Compare the resulting verdict, the specificity of the Evaluator's
`file:line` feedback, and the token cost against this run's numbers in
`sprint-1-run-log.md`. If a genuinely fresh Evaluator reaches the same PASS verdict with
comparably specific feedback, that's real evidence the skill files carry the necessary
context on their own. If it doesn't — if the fresh Evaluator misses something this run's
Evaluator caught only because it remembered writing the code — that's exactly the kind of
gap `.harness/reviews/`'s quality-trend notes exist to surface, and precisely the kind of
finding that should drive a skill file revision.
