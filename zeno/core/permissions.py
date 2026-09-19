"""
Permission engine — decides whether a tool call is allowed to run.

Three tiers, deliberately simple:
  - ALLOW:   runs immediately
  - CONFIRM: runs only if the caller passes confirmed=True (i.e. a human
             said yes). The engine never auto-confirms anything.
  - DENY:    never runs, regardless of confirmation.

Rules are matched by exact tool name first, then by a wildcard "*" default.
This is a policy object, not a UI — something above it (CLI, API layer)
is responsible for actually asking the human when CONFIRM is returned.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


@dataclass
class PermissionEngine:
    rules: dict[str, Decision] = field(default_factory=dict)
    default: Decision = Decision.CONFIRM

    def set_rule(self, tool_name: str, decision: Decision) -> None:
        self.rules[tool_name] = decision

    def evaluate(self, tool_name: str) -> Decision:
        return self.rules.get(tool_name, self.default)

    def check(self, tool_name: str, *, confirmed: bool = False) -> bool:
        """Return True if the tool call may proceed right now."""
        decision = self.evaluate(tool_name)
        if decision == Decision.DENY:
            return False
        if decision == Decision.ALLOW:
            return True
        # CONFIRM
        return confirmed
