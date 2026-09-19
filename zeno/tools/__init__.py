"""
Builds the default ToolRegistry: real tools registered as IMPLEMENTED,
plus a small number of STUB entries for capabilities that are on the
roadmap but not built. The stub list is deliberately short — we'd rather
under-claim and grow it than register 100 fakes.
"""

from __future__ import annotations

from ..memory.layers import MemoryManager
from . import (
    docgen,
    notes,
    proactive,
    projects,
    reminders,
    system_status,
    weather,
    web_search,
)
from .registry import ToolRegistry


def build_default_registry(memory: MemoryManager) -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        "notes.create",
        "Create a note with a title and optional body.",
        lambda **kw: notes.create_note(memory, **kw),
    )
    registry.register(
        "notes.list",
        "List all stored notes.",
        lambda **kw: notes.list_notes(memory, **kw),
    )
    registry.register(
        "notes.delete",
        "Delete a note by id.",
        lambda **kw: notes.delete_note(memory, **kw),
    )

    registry.register(
        "reminders.create",
        "Create a reminder with text and an ISO-8601 due timestamp.",
        lambda **kw: reminders.create_reminder(memory, **kw),
    )
    registry.register(
        "reminders.complete",
        "Mark a reminder as done by id.",
        lambda **kw: reminders.complete_reminder(memory, **kw),
    )
    registry.register(
        "reminders.list_due",
        "List reminders due at or before a given time (defaults to now).",
        lambda **kw: reminders.list_due(memory, **kw),
    )

    registry.register(
        "projects.create",
        "Create a project with a name and optional description.",
        lambda **kw: projects.create_project(memory, **kw),
    )
    registry.register(
        "projects.set_status",
        "Set a project's status to active, paused, or done.",
        lambda **kw: projects.set_status(memory, **kw),
    )
    registry.register(
        "projects.list",
        "List projects, optionally filtered by status.",
        lambda **kw: projects.list_projects(memory, **kw),
    )

    registry.register(
        "weather.current",
        "Fetch current weather for a lat/lon via the Open-Meteo API.",
        weather.get_current_weather,
    )

    registry.register(
        "system.status",
        "Report local CPU, memory, and disk usage.",
        lambda **kw: system_status.get_system_status(),
    )
    registry.register(
        "system.check_thresholds",
        "Given a status dict, return alert strings for anything over threshold.",
        lambda **kw: system_status.check_thresholds(**kw),
    )

    registry.register(
        "web_search.answer",
        "Query DuckDuckGo's Instant Answer API for a fact/definition (not a full search-results list).",
        lambda **kw: web_search.search_instant_answer(**kw),
    )

    registry.register(
        "proactive.morning_briefing",
        "Assemble due reminders (and optional weather, if lat/lon given) into a briefing.",
        lambda **kw: proactive.build_morning_briefing(memory, **kw),
    )
    registry.register(
        "proactive.check_idle",
        "Pure time check: has enough idle time passed to justify a check-in?",
        lambda **kw: proactive.check_idle(**kw),
    )

    registry.register(
        "docgen.pdf",
        "Generate a PDF from a title and a list of (heading, body) sections.",
        lambda **kw: str(docgen.generate_pdf(**kw)),
    )
    registry.register(
        "docgen.pptx",
        "Generate a PPTX from a title and a list of (slide_title, body) slides.",
        lambda **kw: str(docgen.generate_pptx(**kw)),
    )

    # Honest stubs — on the roadmap, not built. Calling .run() raises
    # NotImplementedError on purpose; see registry.py.
    registry.register_stub("device.control", "Control desktop/OS-level actions (open apps, files).")
    registry.register_stub("voice.listen", "Real-time voice input via microphone.")
    registry.register_stub("voice.speak", "Text-to-speech output.")
    registry.register_stub("vision.screen", "Read and reason about the current screen contents.")
    registry.register_stub("sensing.ambient", "Always-on environmental/world sensing.")

    return registry
