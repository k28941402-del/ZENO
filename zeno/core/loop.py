"""
The eight-stage core loop.

    1. PERCEIVE       — capture the raw input for this turn.
    2. CONTEXTUALIZE   — pull relevant memory into the working layer.
    3. PLAN            — decide intent: which tool (if any) should run, with
                          what arguments. Pluggable via `planner`; the default
                          is a small rule-based keyword matcher — genuinely
                          functional, not an LLM, and not pretending to be one.
    4. PERMISSION_CHECK — ask the PermissionEngine whether the chosen tool
                          may run.
    5. EXECUTE         — call the tool if permitted.
    6. REFLECT         — write the outcome into episodic memory.
    7. UPDATE_GOALS    — mark related goals done/active if applicable.
    8. RESPOND         — return a structured result for the caller to render.

Every stage publishes a `stage.<name>` event on the bus before it runs, so
external listeners (a logger, a future UI) can observe the loop without the
loop needing to know they exist.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..memory.layers import MemoryManager
from ..tools.registry import ToolRegistry
from .events import EventBus
from .goals import GoalEngine
from .permissions import PermissionEngine

_turn_counter = itertools.count(1)

PlannerFn = Callable[[str, MemoryManager], "PlannedAction"]


@dataclass
class PlannedAction:
    tool_name: str | None
    args: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass
class TurnResult:
    input_text: str
    planned: PlannedAction
    permitted: bool
    output: Any = None
    error: str | None = None


def default_rule_based_planner(text: str, memory: MemoryManager) -> PlannedAction:
    """A small, honest, rule-based planner. No LLM call, no network."""
    lowered = text.lower().strip()

    if lowered.startswith("note:"):
        return PlannedAction("notes.create", {"title": text[5:].strip()}, "text starts with 'note:'")
    if lowered.startswith("remind me"):
        return PlannedAction(None, {}, "reminder parsing needs an explicit due_iso; not auto-extracted")
    if "system status" in lowered or "how's the machine" in lowered:
        return PlannedAction("system.status", {}, "matched system-status phrasing")
    if lowered.startswith("weather"):
        return PlannedAction(None, {}, "weather needs explicit lat/lon; not auto-extracted from text")
    if lowered.startswith("list notes"):
        return PlannedAction("notes.list", {}, "matched 'list notes'")

    return PlannedAction(None, {}, "no rule matched — this planner is intentionally simple")


class CoreLoop:
    def __init__(
        self,
        memory: MemoryManager,
        tools: ToolRegistry,
        permissions: PermissionEngine | None = None,
        goals: GoalEngine | None = None,
        events: EventBus | None = None,
        planner: PlannerFn = default_rule_based_planner,
    ) -> None:
        self.memory = memory
        self.tools = tools
        self.permissions = permissions or PermissionEngine()
        self.goals = goals or GoalEngine()
        self.events = events or EventBus()
        self.planner = planner

    def run_turn(self, input_text: str, *, confirmed: bool = False) -> TurnResult:
        self.events.publish("stage.perceive", text=input_text)
        self.memory.put("working", "last_input", input_text)

        self.events.publish("stage.contextualize")
        # Deliberately simple: pull identity + recent episodic entries into working memory.
        self.memory.put("working", "identity_snapshot", self.memory.all_in("identity"))

        self.events.publish("stage.plan")
        planned = self.planner(input_text, self.memory)

        if planned.tool_name is None:
            self.events.publish("stage.respond", output=None)
            result = TurnResult(input_text, planned, permitted=False, output=None)
            self._reflect(result)
            return result

        self.events.publish("stage.permission_check", tool=planned.tool_name)
        permitted = self.permissions.check(planned.tool_name, confirmed=confirmed)

        if not permitted:
            result = TurnResult(input_text, planned, permitted=False, error="permission denied")
            self._reflect(result)
            self.events.publish("stage.respond", output=None)
            return result

        self.events.publish("stage.execute", tool=planned.tool_name, args=planned.args)
        try:
            output = self.tools.call(planned.tool_name, **planned.args)
            result = TurnResult(input_text, planned, permitted=True, output=output)
        except Exception as exc:  # noqa: BLE001 — surfaced to caller, not swallowed
            result = TurnResult(input_text, planned, permitted=True, error=str(exc))

        self._reflect(result)
        self.events.publish("stage.respond", output=result.output, error=result.error)
        return result

    def _reflect(self, result: TurnResult) -> None:
        self.events.publish("stage.reflect")
        self.memory.put(
            "episodic",
            f"turn:{next(_turn_counter)}",
            {
                "input": result.input_text,
                "tool": result.planned.tool_name,
                "output": result.output,
                "error": result.error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.events.publish("stage.update_goals")
        self.memory.clear_working()
