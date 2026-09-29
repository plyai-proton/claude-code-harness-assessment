# Run Log — sprint-1 (SLA Breach Alerting)

## Attempt 1

- **Verdict**: PASS
- **Iterations used**: 1 of 3
- **Escalation**: no
- **Estimated token cost**: ~14k tokens (Generator: app-context ~1.1k + architecture-principles
  ~0.9k + coding-conventions ~0.8k + how-to-test ~0.9k + sprint-1-contract ~0.9k + diff
  produced ~2.5k ≈ 7.1k; Evaluator: architecture-principles ~0.9k + how-to-review ~0.9k +
  grading-criteria ~1.1k + generator-summary + diff re-read ~2.5k ≈ 5.4k; Monitor:
  app-context re-read + both files ~1.5k). Order-of-magnitude estimate per
  `monitor.agent.md` — not a billed total.
- **Quality-trend notes**: The Generator's own self-check caught two real defects before
  handoff — a missing `due_at` field propagation in `create_activity`, and a pre-existing
  cross-test-file state-leak in `alert_repository`/`programme_repository` that this
  sprint's new tests exposed. Both were root-caused and fixed (not worked around) within
  attempt 1, so no retry was needed. This is a positive signal for `how-to-test/SKILL.md`
  and `coding-conventions/SKILL.md` as currently written — the Generator had enough
  context to self-correct rather than needing Evaluator feedback to find these. No skill
  file appears under-specified from this run; no changes recommended at this time.

## Sprint summary

- Total attempts: 1
- Final verdict: PASS
- Escalated: no
- Architecture rules exercised: Rule 1 (module boundary — `staff.service.list_users_by_role`
  read pattern), Rule 2 (event-bus-only — both `SLA_BREACH` and `ESCALATION` via
  `event_bus.emit`), Rule 3 (error contract — `ValidationError` on invalid grace period),
  Rule 4 (layer separation). Rule 5 (read-only reports) not applicable — `reports` module
  untouched.
