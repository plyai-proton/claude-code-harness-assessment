"""Business logic for alerts. Other modules must never call create_notification directly —
they emit a 'notification.requested' event on the shared event bus, which this module
subscribes to via register_event_handlers(). This is the enforced event-bus-only boundary.
"""

from __future__ import annotations

from typing import Any

from app.alerts.models import AlertType, Notification, NotificationChannel
from app.alerts.repository import alert_repository
from app.shared.event_bus import event_bus


def list_alerts_for_user(user_id: str) -> list[Notification]:
    return alert_repository.list_for_user(user_id)


def create_notification(
    *,
    alert_type: AlertType,
    recipient_id: str,
    store_id: str,
    message: str,
    channel: NotificationChannel = NotificationChannel.IN_APP,
    related_entity_id: str | None = None,
) -> Notification:
    notification = Notification(
        id=alert_repository.generate_id(),
        type=alert_type,
        channel=channel,
        recipient_id=recipient_id,
        store_id=store_id,
        message=message,
        related_entity_id=related_entity_id,
    )
    return alert_repository.create(notification)


def _handle_notification_requested(payload: dict[str, Any]) -> None:
    create_notification(
        alert_type=AlertType(payload["alert_type"]),
        recipient_id=payload["recipient_id"],
        store_id=payload["store_id"],
        message=payload["message"],
        channel=NotificationChannel(payload.get("channel", NotificationChannel.IN_APP)),
        related_entity_id=payload.get("related_entity_id"),
    )


def register_event_handlers() -> None:
    event_bus.subscribe("notification.requested", _handle_notification_requested)
