"""Business logic for programmes. Also the read-only lookup surface other modules must use
instead of importing app.programmes.repository directly.
"""

from __future__ import annotations

from app.programmes.models import Project, ProjectCreate, ProjectMember, ProjectMemberCreate
from app.programmes.repository import programme_repository
from app.shared.errors import NotFoundError, ValidationError
from app.staff.service import get_user_by_id


def list_programmes(store_id: str) -> list[Project]:
    return programme_repository.list_by_store(store_id)


def get_programme(project_id: str, store_id: str) -> Project:
    project = programme_repository.get(project_id)
    if project is None or project.store_id != store_id:
        raise NotFoundError(f"Programme {project_id} not found")
    return project


def programme_exists(project_id: str, store_id: str) -> bool:
    project = programme_repository.get(project_id)
    return project is not None and project.store_id == store_id


def create_programme(payload: ProjectCreate, *, store_id: str) -> Project:
    project = Project(
        id=programme_repository.generate_id(),
        name=payload.name,
        description=payload.description,
        store_id=store_id,
    )
    return programme_repository.create(project)


def add_member(project_id: str, payload: ProjectMemberCreate, *, store_id: str) -> ProjectMember:
    get_programme(project_id, store_id)
    if get_user_by_id(payload.user_id) is None:
        raise ValidationError(f"User {payload.user_id} does not exist")
    member = ProjectMember(project_id=project_id, user_id=payload.user_id, role=payload.role)
    return programme_repository.add_member(member)
