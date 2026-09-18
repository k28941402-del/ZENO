#!/usr/bin/env python3
"""
Regenerate CAPABILITIES.md straight from the live ToolRegistry.

This is the mechanism that keeps the docs honest: the table below is not
hand-typed anywhere. Run it after adding or changing a tool:

    python scripts/gen_capabilities.py

CI (.github/workflows/ci.yml) re-runs this and fails the build if the
committed CAPABILITIES.md doesn't match what the code actually registers —
so the docs cannot silently drift from reality.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore
from zeno.tools import build_default_registry
from zeno.tools.registry import ToolStatus

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "CAPABILITIES.md"

HEADER = """\
# ZENO — Capability Matrix

**This file is generated from the live tool registry. Do not hand-edit it —
run `python scripts/gen_capabilities.py` instead.** CI fails if this file is
out of date with the code, so it cannot silently drift from what actually
works.

"""


def render() -> str:
    store = SQLiteStore(":memory:")
    memory = MemoryManager(store)
    registry = build_default_registry(memory)

    lines = [HEADER]
    lines.append(f"**{registry.implemented_count()} implemented, {registry.stub_count()} stub.**\n")
    lines.append("| Tool | Status | Description |")
    lines.append("|---|---|---|")
    for spec in registry.list_tools():
        badge = "✅ implemented" if spec.status is ToolStatus.IMPLEMENTED else "🚧 stub (raises `NotImplementedError`)"
        lines.append(f"| `{spec.name}` | {badge} | {spec.description} |")
    lines.append("")
    lines.append(
        "A **stub** is registered so its intended name/shape is visible and "
        "importable, but calling it raises `NotImplementedError` on purpose — "
        "it does not silently pretend to succeed."
    )
    store.close()
    return "\n".join(lines) + "\n"


def main() -> int:
    content = render()
    if "--check" in sys.argv:
        current = OUTPUT_PATH.read_text() if OUTPUT_PATH.exists() else ""
        if current != content:
            print("CAPABILITIES.md is out of date. Run: python scripts/gen_capabilities.py")
            return 1
        print("CAPABILITIES.md is up to date.")
        return 0

    OUTPUT_PATH.write_text(content)
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
