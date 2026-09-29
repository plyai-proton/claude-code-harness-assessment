"""FastAPI dependency for resolving the authenticated user.

Stub bearer-token auth backed by staff.service (in-memory, seeded users) — sufficient to
exercise per-user/per-store authorization rules without a full auth stack. Real auth is
out of scope for this reference project.
"""

from __future__ import annotations

from fastapi import Header

from app.staff.models import User
from app.staff.service import authenticate


def get_current_user(authorization: str = Header(...)) -> User:
    token = authorization.removeprefix("Bearer ").strip()
    return authenticate(token)
