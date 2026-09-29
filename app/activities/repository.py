"""In-memory repository for activities. Only app.activities.service may import this."""

from __future__ import annotations

from datetime import UTC, datetime

from app.activities.models import Task, TaskStatus


class ActivityRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._next_id = 1

    def _new_id(self) -> str:
        task_id = f"task-{self._next_id}"
        self._next_id += 1
        return task_id

    def create(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list_by_store(
        self,
        store_id: str,
        *,
        programme_id: str | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        results = [t for t in self._tasks.values() if t.store_id == store_id]
        if programme_id is not None:
            results = [t for t in results if t.programme_id == programme_id]
        if status is not None:
            results = [t for t in results if t.status == status]
        return sorted(results, key=lambda t: t.created_at)

    def update(self, task: Task) -> Task:
        task.updated_at = datetime.now(UTC)
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def generate_id(self) -> str:
        return self._new_id()


activity_repository = ActivityRepository()
