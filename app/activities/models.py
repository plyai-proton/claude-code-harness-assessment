from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskCategory(StrEnum):
    RESTOCKING = "RESTOCKING"
    PLANOGRAM = "PLANOGRAM"
    AUDIT = "AUDIT"
    COMPLIANCE = "COMPLIANCE"
    GENERAL = "GENERAL"


class Task(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.GENERAL
    store_id: str
    programme_id: str | None = None
    owner_id: str
    assignee_id: str | None = None
    due_at: datetime | None = None
    sla_notified_at: datetime | None = None
    sla_escalated_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.GENERAL
    programme_id: str | None = None
    assignee_id: str | None = None
    due_at: datetime | None = None


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    category: TaskCategory | None = None
    assignee_id: str | None = None


class SlaSweepResult(BaseModel):
    breached: list[str]
    escalated: list[str]
