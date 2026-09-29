"""HTTP layer for activities. Validation and status codes only — no business logic."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.activities import service
from app.activities.models import SlaSweepResult, Task, TaskCreate, TaskStatus, TaskUpdate
from app.shared.auth import get_current_user
from app.staff.models import User

router = APIRouter(prefix="/api/activities", tags=["activities"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[Task])
def list_activities(
    user: CurrentUser,
    programme_id: str | None = None,
    status: TaskStatus | None = None,
) -> list[Task]:
    return service.list_activities(user.store_id, programme_id=programme_id, status=status)


@router.post("", response_model=Task, status_code=201)
def create_activity(payload: TaskCreate, user: CurrentUser) -> Task:
    return service.create_activity(payload, store_id=user.store_id, owner=user)


@router.post("/sla-sweep", response_model=SlaSweepResult)
def run_sla_sweep(user: CurrentUser, grace_period_minutes: int = 60) -> SlaSweepResult:
    return service.run_sla_breach_sweep(user.store_id, grace_period_minutes=grace_period_minutes)


@router.get("/{task_id}", response_model=Task)
def get_activity(task_id: str, user: CurrentUser) -> Task:
    return service.get_activity(task_id, user.store_id)


@router.patch("/{task_id}", response_model=Task)
def update_activity(task_id: str, payload: TaskUpdate, user: CurrentUser) -> Task:
    return service.update_activity(task_id, payload, store_id=user.store_id)


@router.delete("/{task_id}", status_code=204)
def delete_activity(task_id: str, user: CurrentUser) -> None:
    service.delete_activity(task_id, store_id=user.store_id, requester=user)
