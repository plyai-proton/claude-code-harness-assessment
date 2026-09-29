from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectRole(StrEnum):
    STORE_MANAGER = "STORE_MANAGER"
    DEPARTMENT_LEAD = "DEPARTMENT_LEAD"
    ASSOCIATE = "ASSOCIATE"


class Project(BaseModel):
    id: str
    name: str
    description: str | None = None
    store_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectMember(BaseModel):
    project_id: str
    user_id: str
    role: ProjectRole


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectMemberCreate(BaseModel):
    user_id: str
    role: ProjectRole
