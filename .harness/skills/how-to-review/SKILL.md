# Skill: How to Review

Evaluator-specific skill. The procedure for reviewing a Generator attempt: which commands
to run, how to read their output, and how to turn a partial pass into `CONDITIONAL PASS`
vs. `FAIL`. Pairs with `grading-criteria/SKILL.md`, which defines *what* is scored — this
file defines *how* to gather the evidence.

## Step 1 — re-run every automated check independently

Never trust `generator-summary.md`'s self-reported results. Run, in this order, and
capture the raw output verbatim for `evaluator-feedback.md`'s hard gate section:

```
mypy .
ruff check .
python scripts/check_architecture.py
pytest --cov=app --cov-report=term-missing
```

`mypy` and `pytest` exit non-zero on any failure — treat that as an immediate FAIL signal
for the corresponding hard gate (see `grading-criteria/SKILL.md`). `ruff check .` covers
the error-contract hard gate (`TRY002`) alongside general lint. `check_architecture.py`
covers the module-boundary and layer-separation hard gates and prints exact
`path:line` violations when it fails — copy these directly into the file+line feedback
section, don't paraphrase them.

## Step 2 — read the diff for the LLM-assessed rules

The automated checks above cannot see *intent* — they can't tell a legitimate read from
an illegitimate side-effect call. For every new or changed line in `app/*/service.py`:

- If it calls another module's `service.py` function: is the calling function only using
  the return value (a read), or is it triggering a state change in the other module? A
  read is fine. A triggered state change is a Rule 2 (event-bus-only) violation unless it
  goes through `event_bus.emit(...)`.
- If `app/reports/` exists and is touched: confirm no call into another module's
  `create_*`/`update_*`/`delete_*` function (Rule 5).

## Step 3 — check acceptance criteria against actual tests, not against the self-check table

For each GIVEN/WHEN/THEN in the sprint contract:
1. Find the test(s) `generator-summary.md` names for it.
2. Open that test and confirm it asserts the specific business-rule outcome the AC
   describes (see `how-to-test/SKILL.md` — "Asserting business rules, not just status
   codes"). A test that only checks a status code does **not** satisfy the AC, even if
   `generator-summary.md` marked it PASS.
3. If the test doesn't exist, doesn't run, or doesn't assert the right thing, this AC is
   unmet — regardless of what the self-check table claims. Flag the mismatch explicitly in
   `evaluator-feedback.md` if the self-check table overstated a result — this is itself a
   signal worth a quality-trend note for Monitor.

## Step 4 — decide PASS / CONDITIONAL PASS / FAIL

Apply the formula in `grading-criteria/SKILL.md` mechanically — do not override it on
gut feeling. The only place for judgment is Step 2 (reading intent) and Step 3 (checking a
test actually proves an AC); once those checks and the hard gates are settled, the verdict
follows from the formula, not from a fresh holistic impression of the code.

## Writing file+line feedback

Every FAIL or CONDITIONAL PASS item must name a `path:line` and a concrete required
change. Compare:

- **Rejected**: "Error handling needs improvement."
- **Required**: "`app/activities/service.py:52` — `assignee_id` lookup raises
  `ValidationError` correctly, but the message doesn't include the offending ID; sprint
  contract AC #2 requires the message to name it. Update to
  `f\"Assignee {payload.assignee_id} does not exist\"`."

The Generator's retry (per `generator.agent.md`) acts only on what this file names — vague
feedback produces a vague retry, which burns one of the 3 allowed attempts for nothing.
