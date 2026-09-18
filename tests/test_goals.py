import pytest

from zeno.core.goals import GoalEngine, GoalStatus


def test_next_goal_returns_highest_priority():
    engine = GoalEngine()
    engine.add("low priority", priority=1)
    high = engine.add("high priority", priority=10)
    assert engine.next_goal().id == high.id


def test_next_goal_ignores_non_pending():
    engine = GoalEngine()
    goal = engine.add("only goal", priority=5)
    engine.mark(goal.id, GoalStatus.DONE)
    assert engine.next_goal() is None


def test_mark_unknown_goal_raises():
    engine = GoalEngine()
    with pytest.raises(KeyError):
        engine.mark(9999, GoalStatus.DONE)


def test_all_returns_every_goal_regardless_of_status():
    engine = GoalEngine()
    g1 = engine.add("a")
    g2 = engine.add("b")
    engine.mark(g1.id, GoalStatus.CANCELLED)
    assert {g.id for g in engine.all()} == {g1.id, g2.id}
