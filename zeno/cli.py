"""
ZENO CLI — a minimal REPL wiring memory, tools, permissions, the core loop,
and the Delegator together. This is the reference "front end"; anything
richer (voice, a desktop UI) is future work and is listed as such in
CAPABILITIES.md.
"""

from __future__ import annotations

import sys

from .core.delegate import Delegator
from .core.goals import GoalStatus
from .core.loop import CoreLoop
from .core.permissions import Decision, PermissionEngine
from .core.supervisor import build_default_supervisor
from .memory.layers import MemoryManager
from .tools import build_default_registry

BANNER = """\
ZENO — local-first personal intelligence agent (v0.1.0)
Type a command, or ask a question directly. Special commands:
  tools             list every tool and whether it's real or stubbed
  delegate: <task>  queue something up for ZENO to handle on its own
  pending           show what's queued and not yet done
  run pending       have ZENO actually attempt everything queued
  help / quit
"""


def _print_tools(registry) -> None:
    for spec in registry.list_tools():
        print(f"  [{spec.status.value:>11}] {spec.name:<20} {spec.description}")


def _print_pending(delegator: Delegator) -> None:
    pending = [g for g in delegator.goals.all() if g.status is GoalStatus.PENDING]
    if not pending:
        print("  (nothing pending)")
        return
    for g in sorted(pending, key=lambda g: -g.priority):
        print(f"  #{g.id} (priority {g.priority}): {g.description}")


def main() -> None:
    memory = MemoryManager()
    registry = build_default_registry(memory)
    permissions = PermissionEngine(default=Decision.ALLOW)
    supervisor = build_default_supervisor()
    loop = CoreLoop(memory=memory, tools=registry, permissions=permissions, planner=supervisor)
    delegator = Delegator(memory, registry, permissions, supervisor)

    print(BANNER)
    while True:
        try:
            text = input("zeno> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text in ("quit", "exit"):
            break
        if text == "help":
            print(BANNER)
            continue
        if text == "tools":
            _print_tools(registry)
            continue
        if text == "pending":
            _print_pending(delegator)
            continue
        if text.lower().startswith("delegate:"):
            goal = delegator.delegate(text.split(":", 1)[1].strip())
            print(f"  Queued as goal #{goal.id}. It'll run when you say 'run pending'.")
            continue
        if text.lower() == "run pending":
            results = delegator.run_all_pending(confirmed=True)
            if not results:
                print("  (nothing pending)")
            for r in results:
                mark = "done" if r.handled else "still pending"
                print(f"  #{r.goal.id} [{mark}] {r.goal.description!r} — {r.note}")
            continue

        result = loop.run_turn(text, confirmed=True)
        if result.error:
            print(f"  ! {result.error}")
        elif result.planned.tool_name is None:
            print(f"  (no tool matched: {result.planned.reason})")
        else:
            print(f"  -> {result.output}")


if __name__ == "__main__":
    sys.exit(main() or 0)
