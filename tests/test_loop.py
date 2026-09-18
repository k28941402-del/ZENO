import pytest

from zeno.core.loop import CoreLoop, PlannedAction
from zeno.core.permissions import Decision, PermissionEngine
from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore
from zeno.tools import build_default_registry


@pytest.fixture
def loop(tmp_path):
    store = SQLiteStore(tmp_path / "loop.db")
    memory = MemoryManager(store)
    registry = build_default_registry(memory)
    permissions = PermissionEngine(default=Decision.ALLOW)
    yield CoreLoop(memory=memory, tools=registry, permissions=permissions)
    store.close()


def test_note_creation_via_rule_based_planner(loop):
    result = loop.run_turn("note: buy milk")
    assert result.error is None
    assert result.output["title"] == "buy milk"


def test_unmatched_input_returns_no_tool(loop):
    result = loop.run_turn("some input the planner can't classify")
    assert result.planned.tool_name is None
    assert result.output is None


def test_permission_denied_blocks_execution():
    from zeno.tools import build_default_registry as build

    store = SQLiteStore(":memory:")
    memory = MemoryManager(store)
    registry = build(memory)
    permissions = PermissionEngine(default=Decision.DENY)
    loop = CoreLoop(memory=memory, tools=registry, permissions=permissions)

    def planner(text, mem):
        return PlannedAction("system.status", {}, "forced for test")

    loop.planner = planner
    result = loop.run_turn("anything")
    assert result.permitted is False
    assert result.error == "permission denied"


def test_working_memory_cleared_after_turn(loop):
    loop.run_turn("note: temp note")
    assert loop.memory.get("working", "last_input") is None


def test_reflection_writes_episodic_entry(loop):
    loop.run_turn("system status")
    episodic = loop.memory.all_in("episodic")
    assert len(episodic) == 1
