# Skill: Grading Criteria

Evaluator-specific skill. Defines the two weighted dimensions, their hard gates, and the
deterministic formula that converts check results into a `PASS` / `CONDITIONAL PASS` /
`FAIL` verdict. This is the harness's non-deterministic-systems-design component — see
`DESIGN_BRIEF.md` Section C for the walkthrough this skill implements.

## Dimension A — Architecture Compliance (weight 55%)

| # | Check | Type | Source |
|---|---|---|---|
| A1 | Zero cross-module `repository.py` imports | **HARD GATE**, automated | `python scripts/check_architecture.py` (module-boundary check) |
| A2 | Zero raw exception raises in `service.py`/`routes.py` | **HARD GATE**, automated | `ruff check --select TRY002` |
| A3 | No `fastapi` import in any `repository.py`; no `routes.py` importing its own repository | **HARD GATE**, automated | `python scripts/check_architecture.py` (layer-separation check) |
| A4 | New cross-module side effects use `event_bus.emit`, not a direct mutator call | LLM-assessed | Diff review, `how-to-review/SKILL.md` Step 2 |
| A5 | (once `reports` exists) No write call from `reports` into another module | LLM-assessed | Diff review, `how-to-review/SKILL.md` Step 2 |

## Dimension B — Functional Correctness & Test Quality (weight 45%)

| # | Check | Type | Source |
|---|---|---|---|
| B1 | `mypy .` reports 0 errors | **HARD GATE**, automated | `mypy .` |
| B2 | All tests pass; coverage meets thresholds (service ≥80%, routes ≥70%, shared ≥60%, overall ≥70%) | **HARD GATE**, automated | `pytest --cov=app --cov-report=term-missing` |
| B3 | Every sprint AC has a test asserting the business-rule outcome, not just a status code | LLM-assessed | `how-to-review/SKILL.md` Step 3 |
| B4 | `generator-summary.md`'s AC self-check table matches what the tests actually prove | LLM-assessed | `how-to-review/SKILL.md` Step 3 |

## Hard gates always win

Any single hard gate (A1, A2, A3, B1, B2) failing means the sprint verdict is `FAIL`,
full stop — regardless of every other score. This is what makes the verdict
deterministic: **given the same hard-gate results, the verdict never varies.** Hard gates
exist specifically so a sprint can never PASS by having good-looking LLM-assessed scores
paper over a real architecture or correctness break.

## Scoring the LLM-assessed items

Within each dimension, once all hard gates in it pass, each LLM-assessed item is scored:

- **Full credit** — check holds with no exceptions.
- **Half credit** — check holds with one narrow, explicitly-noted caveat (this is what
  produces a `CONDITIONAL PASS` candidate).
- **Zero credit** — check does not hold.

Dimension score = (sum of hard-gate credit, always full once they pass) + (sum of
LLM-assessed item credit), as a fraction of the dimension's total possible credit, scaled
to the dimension's weight.

## Verdict formula

1. **Any hard gate (A1, A2, A3, B1, B2) fails → `FAIL`.** Stop here; do not compute a
   weighted score.
2. Otherwise, compute `total_score = dimension_A_score + dimension_B_score` (0–100).
3. `total_score ≥ 90` and no LLM-assessed item scored zero credit → **`PASS`**.
4. `total_score ≥ 75` (and rule 3 doesn't apply) → **`CONDITIONAL PASS`** — the verdict
   feedback must state each item that scored less than full credit as a "known gap" for
   the developer.
5. `total_score < 75` → **`FAIL`**.

This is deterministic in the sense the case study requires: given the same set of check
results (hard gates + per-item credit), the formula above always produces the same
verdict. The only source of run-to-run variability is the Generator's code itself, which
this formula is explicitly designed to score consistently regardless of *how* the
Evaluator's LLM phrases its reasoning about it.

## Worked example

Sprint: "Add SLA breach alerting." Generator's first attempt: all hard gates pass (A1,
A2, A3, B1, B2). LLM-assessed review finds:
- A4 (event-bus-only): full credit — the sweep correctly emits `notification.requested`.
- A5: not applicable (no `reports` module touched) — excluded from the denominator.
- B3: half credit — 3 of 4 ACs have tests asserting the business outcome; the 4th
  ("escalates to STORE_MANAGER after grace period") only has a test asserting a 200
  response, not that the escalation notification was actually created.
- B4: full credit — self-check table accurately reflects the above.

Dimension A: hard gates full (A1–A3) + A4 full = effectively full marks on the
applicable items → 55/55.
Dimension B: hard gates full (B1–B2) + B3 half + B4 full → B3's shortfall costs half of
one of four items' worth of Dimension B's weight ≈ 45 × (1 − 0.5/4) ≈ 39.4.
`total_score ≈ 55 + 39.4 = 94.4` → but rule 3 requires *no* item at zero credit, which
holds (B3 was half, not zero) — however since B3 didn't reach full credit, the stricter
reading is that this is a `CONDITIONAL PASS` at ~94, with the escalation-notification test
gap stated explicitly, rather than a `PASS`, because an AC (the escalation behavior) is
only partially proven. The Evaluator states this reasoning explicitly rather than letting
the arithmetic alone decide when an AC is only partially demonstrated — see
`how-to-review/SKILL.md` Step 4.
