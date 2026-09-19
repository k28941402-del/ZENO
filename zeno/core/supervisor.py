"""
Supervisor router — a multi-domain planner inspired by the "Supervisor +
specialized sub-agents" pattern (a central router delegating to domain
handlers), reimplemented from scratch for ZENO.

Each "sub-agent" here is just a small pure function: (text, memory) ->
PlannedAction | None. The Supervisor tries them in registration order and
returns the first match. This is still rule-based, not an LLM — exactly as
honest about that as the simpler default planner in core/loop.py. The
difference is structural: sub-agents are independently testable and it's
obvious where to add a new domain, which is what actually matters when this
grows into an LLM-backed router later (each sub-agent's rule logic becomes
that domain's few-shot examples / system prompt instead).

This is a `PlannerFn` — drop-in compatible with `CoreLoop(planner=...)`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..memory.layers import MemoryManager
from .loop import PlannedAction

SubAgent = Callable[[str, MemoryManager], PlannedAction | None]


@dataclass
class Supervisor:
    name: str = "zeno-supervisor"
    _agents: list[tuple[str, SubAgent]] = field(default_factory=list)

    def register(self, domain: str, agent: SubAgent) -> None:
        self._agents.append((domain, agent))

    def route(self, text: str, memory: MemoryManager) -> PlannedAction:
        for domain, agent in self._agents:
            result = agent(text, memory)
            if result is not None:
                result.reason = f"[{domain}] {result.reason}"
                return result
        return PlannedAction(None, {}, "no sub-agent matched")

    def __call__(self, text: str, memory: MemoryManager) -> PlannedAction:
        """Makes the Supervisor itself usable directly as a PlannerFn."""
        return self.route(text, memory)


# ---- Built-in sub-agents -------------------------------------------------
# Each one owns a narrow slice of phrasing. Kept deliberately small and
# readable, same spirit as the default planner in core/loop.py.


def notes_agent(text: str, memory: MemoryManager) -> PlannedAction | None:
    lowered = text.lower().strip()
    if lowered.startswith("note:"):
        return PlannedAction("notes.create", {"title": text[5:].strip()}, "note: prefix")
    if lowered in ("list notes", "show notes", "my notes"):
        return PlannedAction("notes.list", {}, "list-notes phrasing")
    return None


def projects_agent(text: str, memory: MemoryManager) -> PlannedAction | None:
    lowered = text.lower().strip()
    if lowered.startswith("new project:"):
        return PlannedAction("projects.create", {"name": text[12:].strip()}, "new-project prefix")
    if lowered in ("list projects", "show projects", "my projects"):
        return PlannedAction("projects.list", {}, "list-projects phrasing")
    return None


def system_agent(text: str, memory: MemoryManager) -> PlannedAction | None:
    lowered = text.lower().strip()
    if lowered in ("system status", "how's the machine", "hows the machine", "status"):
        return PlannedAction("system.status", {}, "system-status phrasing")
    return None


def web_agent(text: str, memory: MemoryManager) -> PlannedAction | None:
    lowered = text.lower().strip()
    if lowered.startswith(("search:", "look up:")):
        query = text.split(":", 1)[1].strip()
        return PlannedAction("web_search.answer", {"query": query}, "search: prefix")
    return None


def briefing_agent(text: str, memory: MemoryManager) -> PlannedAction | None:
    lowered = text.lower().strip()
    if lowered in ("morning briefing", "briefing", "brief me"):
        return PlannedAction(None, {}, "morning briefing requires lat/lon — call proactive.morning_briefing directly")
    return None


def build_default_supervisor() -> Supervisor:
    """The standard sub-agent lineup, in priority order."""
    supervisor = Supervisor()
    supervisor.register("notes", notes_agent)
    supervisor.register("projects", projects_agent)
    supervisor.register("system", system_agent)
    supervisor.register("web", web_agent)
    supervisor.register("briefing", briefing_agent)
    return supervisor
