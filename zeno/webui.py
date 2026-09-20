"""
ZENO Web UI — a small Flask server exposing the real CoreLoop, Supervisor,
and Delegator over HTTP, with a single-page frontend in webui_static/.

Every endpoint here calls the same objects the CLI (`zeno/cli.py`) uses.
There is no separate "demo" code path — what you see in the browser is
backed by exactly the tool registry documented in CAPABILITIES.md.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests as http_requests
from flask import Flask, jsonify, request, send_from_directory

from .core.delegate import Delegator
from .core.goals import GoalStatus
from .core.loop import CoreLoop
from .core.permissions import Decision, PermissionEngine
from .core.supervisor import build_default_supervisor
from .memory.layers import MemoryManager
from .memory.store import SQLiteStore
from .tools import build_default_registry

if getattr(sys, "frozen", False):
    _STATIC_DIR = Path(sys._MEIPASS) / "zeno" / "webui_static"  # type: ignore[attr-defined]
else:
    _STATIC_DIR = Path(__file__).resolve().parent / "webui_static"


def _serialize_goal(goal) -> dict[str, Any]:
    return {
        "id": goal.id,
        "description": goal.description,
        "priority": goal.priority,
        "status": goal.status.value,
    }


def _serialize_turn_result(result) -> dict[str, Any]:
    return {
        "input": result.input_text,
        "tool": result.planned.tool_name,
        "reason": result.planned.reason,
        "output": result.output,
        "error": result.error,
    }


def _safe_call(registry, tool_name: str, **kwargs: Any) -> Any:
    """Return ``None`` for a degraded dashboard panel, never fake its data."""
    try:
        return registry.call(tool_name, **kwargs)
    except Exception:  # noqa: BLE001 — one unavailable panel must not crash refresh
        return None


def create_app(db_path: str = "zeno_memory.db") -> Flask:
    """Create the app with persistent-by-default, configurable memory.

    HTTP callers must explicitly send ``{"confirmed": true}`` for tools whose
    permission policy is CONFIRM. Delegating or submitting a turn alone never
    grants that confirmation.
    """
    app = Flask(__name__, static_folder=None)

    memory = MemoryManager(SQLiteStore(db_path))
    registry = build_default_registry(memory)
    permissions = PermissionEngine(default=Decision.ALLOW)
    supervisor = build_default_supervisor()
    loop = CoreLoop(memory=memory, tools=registry, permissions=permissions, planner=supervisor)
    delegator = Delegator(memory, registry, permissions, supervisor)

    @app.get("/")
    def index():
        return send_from_directory(_STATIC_DIR, "index.html")

    @app.get("/api/status")
    def status():
        pending = sum(1 for g in delegator.goals.all() if g.status is GoalStatus.PENDING)
        return jsonify({"implemented": registry.implemented_count(), "stub": registry.stub_count(), "pending_goals": pending})

    @app.get("/api/tools")
    def tools():
        return jsonify([{"name": t.name, "status": t.status.value, "description": t.description} for t in registry.list_tools()])

    @app.post("/api/turn")
    def turn():
        data = request.get_json(force=True, silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text is required"}), 400
        result = loop.run_turn(text, confirmed=data.get("confirmed") is True)
        return jsonify(_serialize_turn_result(result))

    @app.get("/api/goals")
    def list_goals():
        return jsonify([_serialize_goal(g) for g in delegator.goals.all()])

    @app.post("/api/delegate")
    def delegate():
        data = request.get_json(force=True, silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "text is required"}), 400
        try:
            priority = int(data.get("priority", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "priority must be an integer"}), 400
        return jsonify(_serialize_goal(delegator.delegate(text, priority=priority)))

    @app.post("/api/run_pending")
    def run_pending():
        data = request.get_json(force=True, silent=True) or {}
        results = delegator.run_all_pending(confirmed=data.get("confirmed") is True)
        return jsonify([{"goal": _serialize_goal(r.goal), "handled": r.handled, "output": r.output, "note": r.note} for r in results])

    @app.get("/api/overview")
    def overview():
        system = _safe_call(registry, "system.status") or {}
        alerts = _safe_call(registry, "system.check_thresholds", status=system) if system else []
        return jsonify({
            "system": system,
            "alerts": alerts or [],
            "due_reminders": _safe_call(registry, "reminders.list_due") or [],
            "notes": _safe_call(registry, "notes.list") or [],
            "projects": _safe_call(registry, "projects.list") or [],
        })

    @app.get("/api/history")
    def history():
        limit = max(0, min(int(request.args.get("limit", 8)), 100))
        items = list(memory.all_in("episodic").values())[-limit:]
        return jsonify(list(reversed(items)))

    @app.post("/api/weather")
    def weather():
        data = request.get_json(force=True, silent=True) or {}
        lat, lon = data.get("latitude"), data.get("longitude")
        if lat is None or lon is None:
            return jsonify({"error": "latitude and longitude are required"}), 400
        try:
            return jsonify(registry.call("weather.current", latitude=float(lat), longitude=float(lon)))
        except (TypeError, ValueError) as exc:
            return jsonify({"error": f"invalid coordinates: {exc}"}), 400
        except Exception as exc:  # noqa: BLE001 — reported honestly
            return jsonify({"error": str(exc)}), 502

    @app.get("/api/godseye/status")
    def godseye_status():
        url = "http://127.0.0.1:4173/"
        try:
            resp = http_requests.get(url, timeout=0.6)
            connected = resp.status_code < 500
        except Exception:  # noqa: BLE001 — not running is normal
            connected = False
        return jsonify({
            "connected": connected,
            "url": url,
            "setup": "cd godseye && cp .env.example .env  # set GOOGLE_MAPS_API_KEY\nnpm install\nnpm run dev -- --host localhost --port 4173",
            "ambient_sensing": "sensing.ambient remains a separate ZENO stub; Godseye reachability does not implement it.",
        })

    return app


def main() -> None:
    app = create_app()
    print("ZENO web UI running at http://127.0.0.1:8420")
    app.run(host="127.0.0.1", port=8420, debug=False)


if __name__ == "__main__":
    main()
