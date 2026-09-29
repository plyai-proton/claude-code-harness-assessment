"""Public read interface for the staff module. Other modules must call this, never
app.staff.repository, to look up user/role information.
"""

from __future__ import annotations

from app.shared.errors import UnauthorizedError
from app.staff.models import StaffRole, User
from app.staff.repository import staff_repository


def get_user_by_id(user_id: str) -> User | None:
    return staff_repository.get_user(user_id)


def authenticate(token: str) -> User:
    user = staff_repository.resolve_token(token)
    if user is None:
        raise UnauthorizedError("Invalid or missing authentication token")
    return user


def list_users_by_role(store_id: str, role: StaffRole) -> list[User]:
    return staff_repository.list_by_store_and_role(store_id, role)
