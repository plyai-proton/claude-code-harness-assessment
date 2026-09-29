# Generator Agent

## Responsibility

Implements exactly one sprint contract's acceptance criteria in working code, respecting
every `architecture-principles` rule the contract names, and self-checks its own work
before handing off to the Evaluator.

## Invocation

Invoked by the orchestrator immediately after developer approval (attempt 1 for the sprint)
or after a `FAIL` verdict (retry — attempts 2 and 3, per `CLAUDE.md`'s 3-attempt cap).

## Skills read (in order)

1. `.harness/skills/app-context/SKILL.md`
2. `.harness/skills/architecture-principles/SKILL.md`
3. `.harness/skills/coding-conventions/SKILL.md` — naming, module layout, typing
   conventions, the `AppError` pattern, the `ruff`/`mypy` configuration in force.
4. `.harness/skills/how-to-test/SKILL.md` — pytest conventions used in this repo, coverage
   thresholds per layer, existing fixtures (`client`, `auth_header`).

## Process

**First attempt:**

1. Read the current `.harness/output/sprint-N-contract.md`.
2. Implement the change across the correct layers only (routes / service / repository, as
   needed by the contract) — never skip a layer, never put logic in the wrong one.
3. Write or extend tests covering every acceptance criterion, following `how-to-test`
   conventions.
4. Run the automated checks locally and fix any failures before handing off:
   ```
   mypy .
   ruff check .
   pytest --cov=app --cov-report=term-missing
   ```
5. Write `.harness/output/generator-summary.md` (format below).

**Retry attempt (after FAIL):**

1. Read `.harness/output/evaluator-feedback.md` instead of re-deriving the sprint from
   scratch.
2. Address only the files and checks `evaluator-feedback.md` names. Do not rewrite files it
   did not flag — a retry is a correction, not a rewrite.
3. Re-run the same automated checks.
4. Overwrite `generator-summary.md` with the updated self-check table, incrementing the
   attempt number and noting what changed since the previous attempt.

## Output contract — `generator-summary.md`

Must contain, in this order:

- Sprint ID and attempt number (1, 2, or 3).
- **AC self-check table** — one row per GIVEN/WHEN/THEN from the sprint contract, each with
  a PASS/FAIL self-assessment and the name of the test that proves it.
- **Files changed** — every path touched, tagged with its layer
  (`routes` / `service` / `repository` / `test` / `other`).
- **Known gaps** — anything not fully satisfied and why. The section must be present even
  when empty (write "None").
- **Automated check results** — literal pass/fail counts for `mypy`, `ruff`, and `pytest`,
  plus the coverage percentage reported.

## What the Generator must never do

- Raise a raw `Exception`, `ValueError`, etc. from `app/*/service.py` or `app/*/routes.py`
  — always a typed subclass of `app.shared.errors.AppError`.
- Import another module's `repository.py`. Cross-module reads go through that module's
  `service.py`; cross-module side effects go through
  `app.shared.event_bus.event_bus.emit(...)` only.
- Put business logic in a `routes.py`, or an HTTP/FastAPI import in a `repository.py`.
- Mark an AC as PASS in its own self-check table without an actual passing test proving it.
