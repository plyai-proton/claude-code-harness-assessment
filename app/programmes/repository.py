"""In-memory repository for programmes. Only app.programmes.service may import this."""

from __future__ import annotations

from app.programmes.models import Project, ProjectMember


class ProgrammeRepository:
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._members: dict[str, list[ProjectMember]] = {}
        self._next_id = 1

    def generate_id(self) -> str:
        project_id = f"programme-{self._next_id}"
        self._next_id += 1
        return project_id

    def create(self, project: Project) -> Project:
        self._projects[project.id] = project
        self._members[project.id] = []
        return project

    def get(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list_by_store(self, store_id: str) -> list[Project]:
        return sorted(
            (p for p in self._projects.values() if p.store_id == store_id),
            key=lambda p: p.created_at,
        )

    def add_member(self, member: ProjectMember) -> ProjectMember:
        self._members.setdefault(member.project_id, []).append(member)
        return member

    def list_members(self, project_id: str) -> list[ProjectMember]:
        return self._members.get(project_id, [])


programme_repository = ProgrammeRepository()
