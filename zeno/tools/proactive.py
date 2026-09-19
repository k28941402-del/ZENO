"""
Proactive tool — the standing-goal-driven behaviors: a morning briefing and
an idle check-in trigger. Both are real logic built entirely on top of
already-implemented tools (weather, reminders, system status); neither one
introduces a new external dependency or a new unverified claim.

`check_idle` is intentionally just a pure time comparison — it does not
itself schedule anything. Actually running it on a timer is the CLI/host
process's job (see README roadmap: "scheduled/proactive runs").
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..memory.layers import MemoryManager
from . import reminders as reminders_tool
from . import weather as weather_tool

WeatherFn = Callable[..., dict[str, Any]]


def build_morning_briefing(
    memory: MemoryManager,
    latitude: float | None = None,
    longitude: float | None = None,
    weather_fn: WeatherFn = weather_tool.get_current_weather,
) -> dict[str, Any]:
    """Assemble a briefing from due reminders + (optionally) current weather.

    Weather is optional: pass latitude/longitude to include it, or omit
    them to get a briefing with just reminders. This mirrors the honesty
    rule elsewhere — no coordinates means no fabricated weather.
    """
    due = reminders_tool.list_due(memory)
    briefing: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),  # noqa: DTZ005 — naive by design, matches reminders.py
        "due_reminders": due,
        "weather": None,
    }
    if latitude is not None and longitude is not None:
        briefing["weather"] = weather_fn(latitude, longitude)
    return briefing


def check_idle(last_interaction: datetime, now: datetime, threshold_minutes: int = 15) -> bool:
    """Return True if enough idle time has passed to justify a check-in.

    Pure function, no side effects — the caller decides what to actually
    do with a True result (e.g. add a goal via GoalEngine).
    """
    elapsed = (now - last_interaction).total_seconds() / 60.0
    return elapsed >= threshold_minutes
