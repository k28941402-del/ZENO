import pytest

from zeno.tools.registry import ToolRegistry


def test_implemented_tool_runs():
    registry = ToolRegistry()
    registry.register("echo", "echoes input", lambda text: text)
    assert registry.call("echo", text="hi") == "hi"


def test_stub_tool_raises_not_implemented():
    registry = ToolRegistry()
    registry.register_stub("future.tool", "not built yet")
    with pytest.raises(NotImplementedError):
        registry.call("future.tool")


def test_duplicate_registration_raises():
    registry = ToolRegistry()
    registry.register("dup", "first", lambda: None)
    with pytest.raises(ValueError):
        registry.register("dup", "second", lambda: None)


def test_counts_match_statuses():
    registry = ToolRegistry()
    registry.register("real", "d", lambda: None)
    registry.register_stub("fake", "d")
    assert registry.implemented_count() == 1
    assert registry.stub_count() == 1


def test_unknown_tool_lookup_raises():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get("nope")
