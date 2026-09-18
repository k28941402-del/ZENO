import pytest

from zeno.core.delegate import Delegator
from zeno.core.goals import GoalStatus
from zeno.core.permissions import Decision, PermissionEngine
from zeno.core.supervisor import build_default_supervisor
from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore
from zeno.tools import build_default_registry


@pytest.fixture
def delegator():
    store = SQLiteStore(":memory:")
    memory = MemoryManager(store)
    registry = build_default_registry(memory)
    permissions = PermissionEngine(default=Decision.ALLOW)
    yield Delegator(memory, registry, permissions, build_default_supervisor())
    store.close()


def test_delegate_queues_without_running(delegator):
    goal = delegator.delegate("note: buy milk")
    assert goal.status == GoalStatus.PENDING
    # nothing has run yet — no episodic/semantic side effect
    assert delegator.memory.all_in("semantic") == {}


def test_run_next_handles_a_solvable_goal(delegator):
    delegator.delegate("note: buy milk")
    result = delegator.run_next(confirmed=True)
    assert result.handled is True
    assert result.output["title"] == "buy milk"
    assert result.goal.status == GoalStatus.DONE


def test_run_next_on_empty_queue_returns_none(delegator):
    assert delegator.run_next() is None


def test_unsolvable_goal_stays_pending_and_is_reported_honestly(delegator):
    delegator.delegate("please water my plants")
    result = delegator.run_next(confirmed=True)
    assert result.handled is False
    assert result.goal.status == GoalStatus.PENDING
    assert "No automatic path" in result.note


def test_confirm_required_tool_stays_pending_without_confirmation():
    store = SQLiteStore(":memory:")
    memory = MemoryManager(store)
    registry = build_default_registry(memory)
    permissions = PermissionEngine(default=Decision.CONFIRM)
    delegator = Delegator(memory, registry, permissions, build_default_supervisor())

    delegator.delegate("note: needs confirmation")
    result = delegator.run_next(confirmed=False)
    assert result.handled is False
    assert "confirmation" in result.note
    assert result.goal.status == GoalStatus.PENDING
    store.close()


def test_run_all_pending_does_not_let_one_bad_goal_block_the_rest(delegator):
    delegator.delegate("please water my plants")  # unsolvable
    delegator.delegate("note: this one works")  # solvable
    results = delegator.run_all_pending(confirmed=True)

    handled = [r for r in results if r.handled]
    unhandled = [r for r in results if not r.handled]
    assert len(handled) == 1
    assert len(unhandled) == 1
    assert handled[0].output["title"] == "this one works"


def test_run_all_pending_respects_priority_order(delegator):
    delegator.delegate("note: low priority", priority=1)
    delegator.delegate("note: high priority", priority=10)
    results = delegator.run_all_pending(confirmed=True)
    assert results[0].output["title"] == "high priority"
    assert results[1].output["title"] == "low priority"


def test_run_all_pending_stops_at_limit(delegator):
    for i in range(5):
        delegator.delegate("please water my plants", priority=i)  # all unsolvable
    results = delegator.run_all_pending(confirmed=True, limit=2)
    assert len(results) == 2
