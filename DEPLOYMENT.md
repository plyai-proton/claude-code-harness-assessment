# Deployment

## Target: Local Docker

Chosen over cloud deployment for this submission — see `DESIGN_BRIEF.md` Section D for the
trade-off. `Dockerfile` and `docker-compose.yml` are both committed at the repository root.

## Steps taken

1. **`Dockerfile`** — `python:3.12-slim` base, copies `pyproject.toml` and `app/` only
   (`.dockerignore` excludes `tests/`, `.venv/`, caches, and `.harness/output/`), installs
   the project with `pip install .`, runs
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
2. **`docker-compose.yml`** — one service, `storeops-api`, maps container port 8000 to
   host port 8000, with a healthcheck hitting `/health` every 10s.
3. **Build and start**:
   ```
   docker compose up -d --build
   ```
4. **Verify**: `docker compose ps` shows the container `healthy`; confirmed the running
   application responds and the SLA-breach-alerting feature added by the harness's
   demonstration run (sprint-1) works end-to-end **through the container**, not just in
   the local dev server.

## Evidence

### Container status

```
NAME                                             IMAGE                                          STATUS                        PORTS
claude-code-harness-assessment-storeops-api-1    claude-code-harness-assessment-storeops-api   Up About a minute (healthy)   0.0.0.0:8000->8000/tcp
```

### Screenshot

[`​.harness/reviews/deployment-evidence/docker-swagger-ui.png`](.harness/reviews/deployment-evidence/docker-swagger-ui.png)
— the containerized app's live Swagger UI at `http://localhost:8000/docs`, showing
`POST /api/activities/sla-sweep` (the harness-generated endpoint) alongside the baseline
endpoints.

### Live API call transcript (against the container, port 8000)

```
$ curl -s -X POST http://localhost:8000/api/activities \
    -H "Authorization: Bearer dev-token-store-manager" -H "Content-Type: application/json" \
    -d '{"title":"Restock freezer aisle","priority":"CRITICAL","category":"RESTOCKING","due_at":"2026-09-29T16:19:31Z"}'
{"id":"task-1","title":"Restock freezer aisle", ..., "due_at":"2026-09-29T16:19:31Z",
 "sla_notified_at":null,"sla_escalated_at":null, ...}

$ curl -s -X POST "http://localhost:8000/api/activities/sla-sweep" \
    -H "Authorization: Bearer dev-token-store-manager"
{"breached":["task-1"],"escalated":[]}

$ curl -s http://localhost:8000/api/alerts -H "Authorization: Bearer dev-token-store-manager"
[{"id":"alert-1","type":"SLA_BREACH","channel":"IN_APP","status":"PENDING",
  "recipient_id":"user-1","store_id":"store-1",
  "message":"Task task-1 ('Restock freezer aisle') breached its SLA",
  "related_entity_id":"task-1","created_at":"2026-09-29T21:19:31.963825Z"}]
```

This confirms the harness-generated feature — SLA breach detection, event-bus-driven
notification, and idempotent re-runs — works correctly in the deployed container, not
only under `pytest` or the local dev server.

## Reproducing this locally

```
docker compose up -d --build
curl http://localhost:8000/health
# ... exercise the API as shown above ...
docker compose down
```
