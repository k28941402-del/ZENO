from zeno.core.supervisor import build_default_supervisor
from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore


def make_memory():
    return MemoryManager(SQLiteStore(":memory:"))


def test_notes_domain_routes_correctly():
    supervisor = build_default_supervisor()
    result = supervisor.route("note: buy milk", make_memory())
    assert result.tool_name == "notes.create"
    assert result.args == {"title": "buy milk"}
    assert "[notes]" in result.reason


def test_projects_domain_routes_correctly():
    supervisor = build_default_supervisor()
    result = supervisor.route("new project: ZENO", make_memory())
    assert result.tool_name == "projects.create"
    assert result.args == {"name": "ZENO"}


def test_system_domain_routes_correctly():
    supervisor = build_default_supervisor()
    result = supervisor.route("system status", make_memory())
    assert result.tool_name == "system.status"


def test_web_domain_extracts_query():
    supervisor = build_default_supervisor()
    result = supervisor.route("search: current mars weather", make_memory())
    assert result.tool_name == "web_search.answer"
    assert result.args == {"query": "current mars weather"}


def test_unmatched_text_falls_through_all_agents():
    supervisor = build_default_supervisor()
    result = supervisor.route("completely unrelated gibberish text", make_memory())
    assert result.tool_name is None
    assert result.reason == "no sub-agent matched"


def test_supervisor_is_directly_usable_as_planner_fn():
    supervisor = build_default_supervisor()
    # CoreLoop calls planner(text, memory) — verify __call__ matches route()
    direct = supervisor.route("note: test", make_memory())
    via_call = supervisor("note: test", make_memory())
    assert direct.tool_name == via_call.tool_name
