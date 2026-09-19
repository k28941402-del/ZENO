"""
Proactive daemon — the actual "runs without being asked" layer.

Pure, testable core: `tick(now)` takes a timestamp and decides what should
fire, based on real elapsed time and real state — never a fabricated
event. `run_forever` is the thin, untestable wrapper that calls `tick` on
a real clock in a real loop; keeping it thin means almost all the logic
lives in code that's covered by tests.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime

ClockFn = Callable[[], datetime]
SleepFn = Callable[[float], None]


@dataclass
class DaemonEvent:
    kind: str  # "morning_briefing" | "idle_checkin"
    at: datetime


@dataclass
class ProactiveDaemon:
    morning_hour: int = 8
    idle_threshold_minutes: int = 15
    _last_briefing_date: date | None = field(default=None, repr=False)
    _last_interaction: datetime | None = field(default=None, repr=False)

    def record_interaction(self, at: datetime) -> None:
        """Call this every time the user actually does something, so idle
        tracking resets. Never fabricates activity — only real turns count."""
        self._last_interaction = at

    def tick(self, now: datetime) -> list[DaemonEvent]:
        events: list[DaemonEvent] = []

        if now.hour >= self.morning_hour and self._last_briefing_date != now.date():
            events.append(DaemonEvent("morning_briefing", now))
            self._last_briefing_date = now.date()

        if self._last_interaction is not None:
            idle_minutes = (now - self._last_interaction).total_seconds() / 60.0
            if idle_minutes >= self.idle_threshold_minutes:
                events.append(DaemonEvent("idle_checkin", now))
                # Reset so we don't fire a check-in every tick while still idle.
                self._last_interaction = now

        return events

    def run_forever(
        self,
        on_event: Callable[[DaemonEvent], None],
        interval_seconds: int = 60,
        clock: ClockFn = datetime.now,
        sleep_fn: SleepFn = time.sleep,
        max_ticks: int | None = None,
    ) -> None:
        """The real, always-on loop. `max_ticks` exists purely so tests can
        bound it; production callers omit it and it runs indefinitely."""
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            for event in self.tick(clock()):
                on_event(event)
            ticks += 1
            if max_ticks is None or ticks < max_ticks:
                sleep_fn(interval_seconds)
