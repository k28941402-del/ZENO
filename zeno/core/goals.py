"""
Goal engine — a small priority-ordered goal queue.

A "goal" here is deliberately lightweight: a description, a priority score,
and a status. The core loop consults it to decide what to work on when
there's no explicit user request in flight (e.g. a standing reminder to
"check calendar every morning"). This is the seed of proactivity, not a
planner — it does not decompose goals into sub-tasks on its own.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from enum import Enum


class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    CANCELLED = "cancelled"


_id_counter = itertools.count(1)


@dataclass
class Goal:
    description: str
    priority: int = 0  # higher = more urgent
    status: GoalStatus = GoalStatus.PENDING
    id: int = field(default_factory=lambda: next(_id_counter))


class GoalEngine:
    def __init__(self) -> None:
        self._goals: dict[int, Goal] = {}

    def add(self, description: str, priority: int = 0) -> Goal:
        goal = Goal(description=description, priority=priority)
        self._goals[goal.id] = goal
        return goal

    def next_goal(self) -> Goal | None:
        pending = [g for g in self._goals.values() if g.status == GoalStatus.PENDING]
        if not pending:
            return None
        return max(pending, key=lambda g: g.priority)

    def mark(self, goal_id: int, status: GoalStatus) -> None:
        if goal_id not in self._goals:
            raise KeyError(f"No such goal id: {goal_id}")
        self._goals[goal_id].status = status

    def all(self) -> list[Goal]:
        return list(self._goals.values())
