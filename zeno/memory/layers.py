"""
Seven-layer memory manager.

    working    — current-turn scratch space. In-memory only, cleared every turn.
    session    — current conversation context. In-memory only, cleared on new_session().
    episodic   — timestamped record of things that happened. Persisted.
    semantic   — standalone facts ("user's timezone is X"). Persisted.
    procedural — learned routines ("how the user likes reports formatted"). Persisted.
    reflective — the agent's own summaries/notes about past interactions. Persisted.
    identity   — stable profile info (name, preferences). Persisted.

The persisted layers all share one SQLiteStore instance (memory/store.py).
The two ephemeral layers are plain dicts — there is no vector search here,
no embeddings, no recency-weighted retrieval. Anything beyond exact key
lookup is future work, and this docstring says so rather than pretending
otherwise.
"""

from __future__ import annotations

from typing import Any

from .store import SQLiteStore

_PERSISTED_LAYERS = ("episodic", "semantic", "procedural", "reflective", "identity")
_EPHEMERAL_LAYERS = ("working", "session")
ALL_LAYERS = _EPHEMERAL_LAYERS + _PERSISTED_LAYERS


class MemoryManager:
    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()
        self._ephemeral: dict[str, dict[str, Any]] = {layer: {} for layer in _EPHEMERAL_LAYERS}

    def put(self, layer: str, key: str, value: Any) -> None:
        self._validate_layer(layer)
        if layer in _EPHEMERAL_LAYERS:
            self._ephemeral[layer][key] = value
        else:
            self.store.put(layer, key, value)

    def get(self, layer: str, key: str) -> Any | None:
        self._validate_layer(layer)
        if layer in _EPHEMERAL_LAYERS:
            return self._ephemeral[layer].get(key)
        return self.store.get(layer, key)

    def all_in(self, layer: str) -> dict[str, Any]:
        self._validate_layer(layer)
        if layer in _EPHEMERAL_LAYERS:
            return dict(self._ephemeral[layer])
        return self.store.all_in_layer(layer)

    def clear_working(self) -> None:
        self._ephemeral["working"] = {}

    def new_session(self) -> None:
        self._ephemeral["session"] = {}

    def _validate_layer(self, layer: str) -> None:
        if layer not in ALL_LAYERS:
            raise ValueError(f"Unknown memory layer '{layer}'. Valid layers: {ALL_LAYERS}")
