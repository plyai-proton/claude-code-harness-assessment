"""Public read interface for the staff module. Other modules must call this, never
app.staff.repository, to look up user/role information.
"""

from __future__ import annotations

from app.shared.errors import UnauthorizedError
from app.staff.models import User
from app.staff.repository import staff_repository


def get_user_by_id(user_id: str) -> User | None:
    return staff_repository.get_user(user_id)


def authenticate(token: str) -> User:
    user = staff_repository.resolve_token(token)
    if user is None:
        raise UnauthorizedError("Invalid or missing authentication token")
    return user
