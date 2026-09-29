from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AlertType(StrEnum):
    INVENTORY = "INVENTORY"
    SLA_BREACH = "SLA_BREACH"
    SHIFT_HANDOVER = "SHIFT_HANDOVER"
    ESCALATION = "ESCALATION"


class NotificationChannel(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"


class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    READ = "READ"
    FAILED = "FAILED"


class Notification(BaseModel):
    id: str
    type: AlertType
    channel: NotificationChannel = NotificationChannel.IN_APP
    status: NotificationStatus = NotificationStatus.PENDING
    recipient_id: str
    store_id: str
    message: str
    related_entity_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
