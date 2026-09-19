"""Notes tool — real CRUD, persisted via the semantic memory layer."""

from __future__ import annotations

import itertools
from typing import Any

from ..memory.layers import MemoryManager

_id_counter = itertools.count(1)
_LAYER = "semantic"
_PREFIX = "note:"


def _key(note_id: int) -> str:
    return f"{_PREFIX}{note_id}"


def create_note(memory: MemoryManager, title: str, body: str = "") -> dict[str, Any]:
    note_id = next(_id_counter)
    note = {"id": note_id, "title": title, "body": body}
    memory.put(_LAYER, _key(note_id), note)
    return note


def get_note(memory: MemoryManager, note_id: int) -> dict[str, Any] | None:
    return memory.get(_LAYER, _key(note_id))


def list_notes(memory: MemoryManager) -> list[dict[str, Any]]:
    items = memory.all_in(_LAYER)
    return [v for k, v in items.items() if k.startswith(_PREFIX)]


def delete_note(memory: MemoryManager, note_id: int) -> bool:
    if memory.get(_LAYER, _key(note_id)) is None:
        return False
    memory.store.delete(_LAYER, _key(note_id))
    return True
