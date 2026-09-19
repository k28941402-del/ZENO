"""
Tool registry.

The whole point of this file: every tool declares a status when it's
registered, and nothing else in the codebase is allowed to claim a tool
does something the registry doesn't say it does. `list_tools()` is what
the README's capability table is generated from — see scripts/gen_capabilities.py.

Statuses:
    IMPLEMENTED — calling .run() executes real logic and can fail for real reasons.
    STUB        — .run() raises NotImplementedError. Registered so the shape of
                  the eventual tool (name, description, args) is visible and
                  testable, but it does not pretend to work.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ToolStatus(str, Enum):
    IMPLEMENTED = "implemented"
    STUB = "stub"


@dataclass
class ToolSpec:
    name: str
    description: str
    status: ToolStatus
    handler: Callable[..., Any]

    def run(self, **kwargs: Any) -> Any:
        if self.status is ToolStatus.STUB:
            raise NotImplementedError(
                f"Tool '{self.name}' is registered as a STUB and has no real implementation yet."
            )
        return self.handler(**kwargs)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        status: ToolStatus = ToolStatus.IMPLEMENTED,
    ) -> ToolSpec:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        spec = ToolSpec(name=name, description=description, status=status, handler=handler)
        self._tools[name] = spec
        return spec

    def register_stub(self, name: str, description: str) -> ToolSpec:
        def _not_built(**_kwargs: Any) -> Any:
            raise NotImplementedError(name)

        return self.register(name, description, _not_built, status=ToolStatus.STUB)

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"No such tool: {name}")
        return self._tools[name]

    def call(self, name: str, **kwargs: Any) -> Any:
        return self.get(name).run(**kwargs)

    def list_tools(self) -> list[ToolSpec]:
        return sorted(self._tools.values(), key=lambda t: t.name)

    def implemented_count(self) -> int:
        return sum(1 for t in self._tools.values() if t.status is ToolStatus.IMPLEMENTED)

    def stub_count(self) -> int:
        return sum(1 for t in self._tools.values() if t.status is ToolStatus.STUB)
