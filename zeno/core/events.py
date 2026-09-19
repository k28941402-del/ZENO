"""
Event bus — a minimal synchronous publish/subscribe system.

Every stage of the core loop publishes an event when it starts and finishes.
Tools, memory layers, and external listeners (loggers, a future UI) can
subscribe without the core loop needing to know they exist.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Event:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


Listener = Callable[[Event], None]


class EventBus:
    """A tiny synchronous event bus. No external dependencies, no async."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self._history: list[Event] = []
        self._history_limit = 500

    def subscribe(self, event_name: str, listener: Listener) -> None:
        self._listeners[event_name].append(listener)

    def unsubscribe(self, event_name: str, listener: Listener) -> None:
        if listener in self._listeners.get(event_name, []):
            self._listeners[event_name].remove(listener)

    def publish(self, event_name: str, **payload: Any) -> Event:
        event = Event(name=event_name, payload=payload)
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history.pop(0)
        for listener in list(self._listeners.get(event_name, [])):
            listener(event)
        for listener in list(self._listeners.get("*", [])):
            listener(event)
        return event

    def history(self, event_name: str | None = None) -> list[Event]:
        if event_name is None:
            return list(self._history)
        return [e for e in self._history if e.name == event_name]
