"""In-process synchronous event bus. The only permitted channel for cross-module side effects.

A module must never import another module's service or repository to trigger a side effect
in it (e.g. creating a Notification from the activities module). It must emit an event here;
the owning module subscribes and reacts. Reads (not side effects) may go through the target
module's service layer directly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = {}

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._subscribers.setdefault(event_name, []).append(handler)

    def emit(self, event_name: str, payload: dict[str, Any]) -> None:
        for handler in self._subscribers.get(event_name, []):
            handler(payload)


event_bus = EventBus()
