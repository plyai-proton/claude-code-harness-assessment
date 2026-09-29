from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.activities.routes import router as activities_router
from app.alerts import service as alerts_service
from app.alerts.routes import router as alerts_router
from app.programmes.routes import router as programmes_router
from app.shared.errors import AppError

app = FastAPI(title="StoreOps API", version="0.1.0")

app.include_router(activities_router)
app.include_router(programmes_router)
app.include_router(alerts_router)

alerts_service.register_event_handlers()


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
