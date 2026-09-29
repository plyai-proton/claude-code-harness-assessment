# StoreOps Claude Code Development Harness

**Repository**: https://github.com/plyai-proton/claude-code-harness-assessment

Capstone submission for Cognizant Skillspring's AI-Native Tech Architect Programme —
Build Track, Case Study 1: *Build a Working Claude Code Development Harness*.

A governed, multi-agent Claude Code harness (Planner → Generator → Evaluator → Monitor)
that enforces architectural standards on AI-generated code for **StoreOps**, a retail
store operations REST API (Python 3.12 / FastAPI), and a live demonstration run adding
SLA breach alerting to it end-to-end.

## Quick facts

| | |
|---|---|
| Stack | Python 3.12, FastAPI, pytest, mypy (strict), ruff |
| Harness | `CLAUDE.md` + 4 agents + 7 skill files + a 2-dimension weighted evaluation framework |
| Demonstration feature | SLA breach alerting (`POST /api/activities/sla-sweep`) |
| Deployment | Local Docker (`docker compose up -d --build`) |
| Coverage | 97% overall (thresholds: service ≥80%, routes ≥70%, shared ≥60%, overall ≥70%) |

## Start here

| Document | Covers |
|---|---|
| [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) | Intent decomposition, governance framework, non-determinism strategy, architectural decisions |
| [`REFLECTION.md`](REFLECTION.md) | What worked, what didn't, one concrete next step |
| [`JOURNAL.md`](JOURNAL.md) | Trade-offs recorded as they were made, phase by phase |
| [`CLAUDE.md`](CLAUDE.md) | The harness orchestrator itself |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Docker deployment steps and live evidence |

## Repository layout

```
CLAUDE.md, PROMPT.md, DEPLOYMENT.md, DESIGN_BRIEF.md, REFLECTION.md, JOURNAL.md
Dockerfile, docker-compose.yml, pyproject.toml

.harness/
  agents/    planner / generator / evaluator / monitor .agent.md
  skills/    7 skill files (app-context, architecture-principles, sprint-decomposition,
             coding-conventions, how-to-test, how-to-review, grading-criteria)
  reviews/   the committed governance audit trail for the demonstration sprint
             (spec, sprint contract, generator summary, evaluator feedback, run log,
             deployment screenshots)

app/         StoreOps source — activities, programmes, staff, alerts modules,
             each Routes -> Service -> Repository
scripts/     check_architecture.py — automated module-boundary / layer-separation hard gates
tests/       mirrors app/
```

## Running it locally

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest --cov=app --cov-report=term-missing
.venv/bin/uvicorn app.main:app --reload   # http://localhost:8000/docs
```

Or via Docker:

```bash
docker compose up -d --build
curl http://localhost:8000/health
```

See [`.harness/reviews/`](.harness/reviews/) for the full chain of evidence from the
demonstration run — feature prompt → spec → sprint contract → generated code →
evaluator verdict → archived run log.

## License

[MIT](LICENSE)
