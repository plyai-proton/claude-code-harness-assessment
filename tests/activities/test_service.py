from __future__ import annotations

import pytest

from app.activities import service
from app.activities.models import TaskCreate
from app.shared.errors import ForbiddenError, ValidationError
from app.staff.models import StaffRole, User

# Repository reset between tests is handled by tests/conftest.py's autouse
# _reset_module_state fixture.


def _user(role: StaffRole = StaffRole.ASSOCIATE, user_id: str = "user-2") -> User:
    return User(id=user_id, name="Test User", email="t@example.com", store_id="store-1", role=role)


def test_create_activity_rejects_unknown_assignee() -> None:
    with pytest.raises(ValidationError):
        service.create_activity(
            TaskCreate(title="X", assignee_id="ghost"), store_id="store-1", owner=_user()
        )


def test_delete_activity_by_non_owner_associate_raises_forbidden() -> None:
    owner = _user(role=StaffRole.ASSOCIATE, user_id="user-2")
    other = _user(role=StaffRole.ASSOCIATE, user_id="user-3")
    task = service.create_activity(TaskCreate(title="X"), store_id="store-1", owner=owner)
    with pytest.raises(ForbiddenError):
        service.delete_activity(task.id, store_id="store-1", requester=other)
