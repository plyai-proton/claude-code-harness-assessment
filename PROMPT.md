# Demonstration Run — Feature Prompt

Entered as the developer's harness-invoking message, per `CLAUDE.md` § Entry prompt format:

```
@planner Add SLA breach alerting — when a HIGH or CRITICAL task passes its due date
without reaching DONE, automatically fire an SLA_BREACH notification to the assigned
staff member and escalate to every STORE_MANAGER at that store if unresolved after a
configurable grace period.
```

This is one of the four suggested demonstration features in the case study (Section 3.4).
It was chosen because it exercises all five architecture rules that matter to this
codebase at once: it creates a cross-module side effect (activities → alerts) that must
go through the event bus (Rule 2), reads staff role data across a module boundary that
must go through `staff.service` (Rule 1), must raise typed errors for invalid input
(Rule 3), and requires correct layer separation for a new endpoint (Rule 4). It does not
touch `reports`, so Rule 5 does not apply to this run.
