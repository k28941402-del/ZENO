"""
SQLite-backed key-value store. One table, namespaced by "layer", so the
seven memory layers in layers.py all persist through this single file.
No ORM — this is intentionally small enough to read in one sitting.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, path: str | Path = "zeno_memory.db") -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                layer TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (layer, key)
            )
            """
        )
        self._conn.commit()

    def put(self, layer: str, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT INTO memory (layer, key, value, created_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(layer, key) DO UPDATE SET value=excluded.value, created_at=excluded.created_at",
            (layer, key, json.dumps(value), datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def get(self, layer: str, key: str) -> Any | None:
        row = self._conn.execute(
            "SELECT value FROM memory WHERE layer = ? AND key = ?", (layer, key)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, layer: str, key: str) -> None:
        self._conn.execute("DELETE FROM memory WHERE layer = ? AND key = ?", (layer, key))
        self._conn.commit()

    def all_in_layer(self, layer: str) -> dict[str, Any]:
        rows = self._conn.execute(
            "SELECT key, value FROM memory WHERE layer = ? ORDER BY created_at", (layer,)
        ).fetchall()
        return {k: json.loads(v) for k, v in rows}

    def close(self) -> None:
        self._conn.close()
