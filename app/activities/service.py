"""Business logic for activities. Routes must never touch the repository directly."""

from __future__ import annotations

from app.activities.models import Task, TaskCreate, TaskStatus, TaskUpdate
from app.activities.repository import activity_repository
from app.shared.errors import ForbiddenError, NotFoundError, ValidationError
from app.staff.models import StaffRole, User
from app.staff.service import get_user_by_id

_MANAGER_ROLES = {StaffRole.STORE_MANAGER, StaffRole.REGIONAL_MANAGER}


def list_activities(
    store_id: str,
    *,
    programme_id: str | None = None,
    status: TaskStatus | None = None,
) -> list[Task]:
    return activity_repository.list_by_store(store_id, programme_id=programme_id, status=status)


def get_activity(task_id: str, store_id: str) -> Task:
    task = activity_repository.get(task_id)
    if task is None or task.store_id != store_id:
        raise NotFoundError(f"Activity {task_id} not found")
    return task


def create_activity(payload: TaskCreate, *, store_id: str, owner: User) -> Task:
    if payload.assignee_id is not None and get_user_by_id(payload.assignee_id) is None:
        raise ValidationError(f"Assignee {payload.assignee_id} does not exist")
    task = Task(
        id=activity_repository.generate_id(),
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        programme_id=payload.programme_id,
        store_id=store_id,
        owner_id=owner.id,
        assignee_id=payload.assignee_id,
    )
    return activity_repository.create(task)


def update_activity(task_id: str, payload: TaskUpdate, *, store_id: str) -> Task:
    task = get_activity(task_id, store_id)
    if payload.status is not None:
        task.status = payload.status
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.category is not None:
        task.category = payload.category
    if payload.assignee_id is not None:
        if get_user_by_id(payload.assignee_id) is None:
            raise ValidationError(f"Assignee {payload.assignee_id} does not exist")
        task.assignee_id = payload.assignee_id
    return activity_repository.update(task)


def delete_activity(task_id: str, *, store_id: str, requester: User) -> None:
    task = get_activity(task_id, store_id)
    is_owner = task.owner_id == requester.id
    is_manager = requester.role in _MANAGER_ROLES
    if not is_owner and not is_manager:
        raise ForbiddenError("Only the owner or a store manager may delete this activity")
    activity_repository.delete(task_id)
