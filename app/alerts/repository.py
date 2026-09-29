"""In-memory repository for alerts. Only app.alerts.service may import this."""

from __future__ import annotations

from app.alerts.models import Notification


class AlertRepository:
    def __init__(self) -> None:
        self._notifications: dict[str, Notification] = {}
        self._next_id = 1

    def generate_id(self) -> str:
        notification_id = f"alert-{self._next_id}"
        self._next_id += 1
        return notification_id

    def create(self, notification: Notification) -> Notification:
        self._notifications[notification.id] = notification
        return notification

    def list_for_user(self, user_id: str) -> list[Notification]:
        return sorted(
            (n for n in self._notifications.values() if n.recipient_id == user_id),
            key=lambda n: n.created_at,
            reverse=True,
        )


alert_repository = AlertRepository()
