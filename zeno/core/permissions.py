"""Permission engine — decides whether a tool call is allowed to run.

Three tiers are deliberately simple:
- ALLOW: runs immediately.
- CONFIRM: runs only when the caller passes ``confirmed=True``.
- DENY: never runs, regardless of confirmation.

Rules match an exact tool name first, then the ``*`` wildcard rule, then the
engine default. The engine never auto-confirms anything.
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
        """Return the most specific configured policy for ``tool_name``."""
        return self.rules.get(tool_name, self.rules.get("*", self.default))

    def check(self, tool_name: str, *, confirmed: bool = False) -> bool:
        """Return True if the tool call may proceed right now."""
        decision = self.evaluate(tool_name)
        if decision is Decision.DENY:
            return False
        if decision is Decision.ALLOW:
            return True
        return confirmed
