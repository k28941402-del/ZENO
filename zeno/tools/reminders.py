"""Reminders tool — real CRUD with due-date comparisons, persisted via memory."""

from __future__ import annotations

import itertools
from datetime import datetime
from typing import Any

from ..memory.layers import MemoryManager

_id_counter = itertools.count(1)
_LAYER = "procedural"
_PREFIX = "reminder:"


def _key(reminder_id: int) -> str:
    return f"{_PREFIX}{reminder_id}"


def create_reminder(memory: MemoryManager, text: str, due_iso: str) -> dict[str, Any]:
    # Validate the ISO timestamp early rather than storing something unusable.
    datetime.fromisoformat(due_iso)
    reminder_id = next(_id_counter)
    reminder = {"id": reminder_id, "text": text, "due": due_iso, "done": False}
    memory.put(_LAYER, _key(reminder_id), reminder)
    return reminder


def complete_reminder(memory: MemoryManager, reminder_id: int) -> dict[str, Any] | None:
    reminder = memory.get(_LAYER, _key(reminder_id))
    if reminder is None:
        return None
    reminder["done"] = True
    memory.put(_LAYER, _key(reminder_id), reminder)
    return reminder


def list_due(memory: MemoryManager, as_of_iso: str | None = None) -> list[dict[str, Any]]:
    # Naive datetimes throughout: due_iso is caller-supplied local time, not
    # normalized to UTC. Documented limitation, not an oversight — see
    # CAPABILITIES.md / README known limitations.
    as_of = datetime.fromisoformat(as_of_iso) if as_of_iso else datetime.now()  # noqa: DTZ005
    items = memory.all_in(_LAYER)
    due = []
    for key, reminder in items.items():
        if not key.startswith(_PREFIX) or reminder["done"]:
            continue
        if datetime.fromisoformat(reminder["due"]) <= as_of:
            due.append(reminder)
    return sorted(due, key=lambda r: r["due"])
