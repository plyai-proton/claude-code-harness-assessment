"""In-memory repository. Other modules must never import this directly (read-only for other
modules is provided exclusively via staff.service).
"""

from __future__ import annotations

from app.staff.models import AuthToken, StaffRole, User


class StaffRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._tokens: dict[str, AuthToken] = {}
        self._seed()

    def _seed(self) -> None:
        seed_users = [
            User(
                id="user-1",
                name="Alex Rivera",
                email="alex.rivera@storeops.example",
                store_id="store-1",
                role=StaffRole.STORE_MANAGER,
            ),
            User(
                id="user-2",
                name="Jordan Lee",
                email="jordan.lee@storeops.example",
                store_id="store-1",
                role=StaffRole.ASSOCIATE,
            ),
            User(
                id="user-3",
                name="Sam Patel",
                email="sam.patel@storeops.example",
                store_id="store-1",
                role=StaffRole.DEPARTMENT_LEAD,
            ),
        ]
        seed_tokens = [
            AuthToken(token="dev-token-store-manager", user_id="user-1"),
            AuthToken(token="dev-token-associate", user_id="user-2"),
            AuthToken(token="dev-token-department-lead", user_id="user-3"),
        ]
        for user in seed_users:
            self._users[user.id] = user
        for token in seed_tokens:
            self._tokens[token.token] = token

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def resolve_token(self, token: str) -> User | None:
        auth_token = self._tokens.get(token)
        if auth_token is None:
            return None
        return self._users.get(auth_token.user_id)


staff_repository = StaffRepository()
