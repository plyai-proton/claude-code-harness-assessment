from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class StaffRole(StrEnum):
    REGIONAL_MANAGER = "REGIONAL_MANAGER"
    STORE_MANAGER = "STORE_MANAGER"
    DEPARTMENT_LEAD = "DEPARTMENT_LEAD"
    ASSOCIATE = "ASSOCIATE"


class User(BaseModel):
    id: str
    name: str
    email: str
    store_id: str
    role: StaffRole


class AuthToken(BaseModel):
    token: str
    user_id: str
