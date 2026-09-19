"""Projects tool — real CRUD with a small status lifecycle, persisted via memory."""

from __future__ import annotations

import itertools
from typing import Any

from ..memory.layers import MemoryManager

_id_counter = itertools.count(1)
_LAYER = "procedural"
_PREFIX = "project:"
_VALID_STATUSES = {"active", "paused", "done"}


def _key(project_id: int) -> str:
    return f"{_PREFIX}{project_id}"


def create_project(memory: MemoryManager, name: str, description: str = "") -> dict[str, Any]:
    project_id = next(_id_counter)
    project = {"id": project_id, "name": name, "description": description, "status": "active"}
    memory.put(_LAYER, _key(project_id), project)
    return project


def set_status(memory: MemoryManager, project_id: int, status: str) -> dict[str, Any] | None:
    if status not in _VALID_STATUSES:
        raise ValueError(f"status must be one of {_VALID_STATUSES}, got '{status}'")
    project = memory.get(_LAYER, _key(project_id))
    if project is None:
        return None
    project["status"] = status
    memory.put(_LAYER, _key(project_id), project)
    return project


def list_projects(memory: MemoryManager, status: str | None = None) -> list[dict[str, Any]]:
    items = memory.all_in(_LAYER)
    projects = [v for k, v in items.items() if k.startswith(_PREFIX)]
    if status is not None:
        projects = [p for p in projects if p["status"] == status]
    return projects
