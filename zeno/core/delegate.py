"""
Delegator — "hand ZENO something you don't want to do yourself."

This is the layer that actually earns the JARVIS comparison: you say what
you want handled, it goes on the GoalEngine's queue, and `run_next` /
`run_all_pending` try to actually do it using real, implemented tools —
routed the same way normal input is, through a Supervisor/PlannerFn.

The honesty rule from the rest of this codebase applies here without
exception: if nothing in the tool registry can satisfy a delegated task,
the Delegator does NOT pretend to have done it. The goal stays PENDING and
the result says plainly that there's no automatic path for it yet — that's
the difference between "proactive" and "fabricating success."

Anything a tool call needs a human sign-off for (via PermissionEngine's
CONFIRM tier) requires an explicit `confirmed=True` from the caller — the
Delegator never auto-confirms actions on your behalf, even when you've
asked it to "just handle it." Confirmation is deliberately separated from
delegation so "handle this for me" can never silently become "send this
without me looking."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..memory.layers import MemoryManager
from ..tools.registry import ToolRegistry
from .goals import Goal, GoalEngine, GoalStatus
from .loop import PlannedAction, PlannerFn
from .permissions import PermissionEngine


@dataclass
class DelegationResult:
    goal: Goal
    handled: bool
    output: Any = None
    note: str = ""


class Delegator:
    def __init__(
        self,
        memory: MemoryManager,
        tools: ToolRegistry,
        permissions: PermissionEngine,
        planner: PlannerFn,
        goals: GoalEngine | None = None,
    ) -> None:
        self.memory = memory
        self.tools = tools
        self.permissions = permissions
        self.planner = planner
        self.goals = goals or GoalEngine()

    def delegate(self, description: str, priority: int = 0) -> Goal:
        """Queue something up. Returns immediately — nothing runs yet."""
        return self.goals.add(description, priority=priority)

    def run_next(self, *, confirmed: bool = False) -> DelegationResult | None:
        """Attempt the single highest-priority pending goal. Returns None if
        the queue is empty."""
        goal = self.goals.next_goal()
        if goal is None:
            return None
        return self._attempt(goal, confirmed=confirmed)

    def run_all_pending(self, *, confirmed: bool = False, limit: int = 50) -> list[DelegationResult]:
        """Attempt every pending goal, in priority order, up to `limit`
        attempts (safety valve, not an expected ceiling). Unlike calling
        `run_next` in a loop, a goal that can't be handled yet doesn't block
        goals behind it — it's skipped for the rest of this pass rather than
        retried forever, since nothing changes about *why* it failed by
        asking again immediately."""
        results: list[DelegationResult] = []
        skipped_ids: set[int] = set()

        for _ in range(limit):
            candidates = [
                g for g in self.goals.all() if g.status is GoalStatus.PENDING and g.id not in skipped_ids
            ]
            if not candidates:
                break
            goal = max(candidates, key=lambda g: g.priority)

            result = self._attempt(goal, confirmed=confirmed)
            results.append(result)
            if not result.handled:
                skipped_ids.add(goal.id)

        return results

    def _attempt(self, goal: Goal, *, confirmed: bool) -> DelegationResult:
        self.goals.mark(goal.id, GoalStatus.ACTIVE)
        planned: PlannedAction = self.planner(goal.description, self.memory)

        if planned.tool_name is None:
            self.goals.mark(goal.id, GoalStatus.PENDING)
            return DelegationResult(
                goal=goal,
                handled=False,
                note=f"No automatic path for this yet ({planned.reason}). Left pending.",
            )

        if not self.permissions.check(planned.tool_name, confirmed=confirmed):
            self.goals.mark(goal.id, GoalStatus.PENDING)
            return DelegationResult(
                goal=goal,
                handled=False,
                note=f"'{planned.tool_name}' needs your confirmation before it can run. Left pending.",
            )

        try:
            output = self.tools.call(planned.tool_name, **planned.args)
        except Exception as exc:  # noqa: BLE001 — surfaced honestly, not swallowed
            self.goals.mark(goal.id, GoalStatus.PENDING)
            return DelegationResult(
                goal=goal,
                handled=False,
                output=None,
                note=f"Tried '{planned.tool_name}' and it failed: {exc}. Left pending.",
            )

        self.goals.mark(goal.id, GoalStatus.DONE)
        return DelegationResult(goal=goal, handled=True, output=output, note=f"Handled via '{planned.tool_name}'.")
