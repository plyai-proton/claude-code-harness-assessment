from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.programmes import service
from app.programmes.models import Project, ProjectCreate, ProjectMember, ProjectMemberCreate
from app.shared.auth import get_current_user
from app.staff.models import User

router = APIRouter(prefix="/api/programmes", tags=["programmes"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[Project])
def list_programmes(user: CurrentUser) -> list[Project]:
    return service.list_programmes(user.store_id)


@router.post("", response_model=Project, status_code=201)
def create_programme(payload: ProjectCreate, user: CurrentUser) -> Project:
    return service.create_programme(payload, store_id=user.store_id)


@router.post("/{project_id}/members", response_model=ProjectMember, status_code=201)
def add_member(
    project_id: str, payload: ProjectMemberCreate, user: CurrentUser
) -> ProjectMember:
    return service.add_member(project_id, payload, store_id=user.store_id)
