import pytest

from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore


@pytest.fixture
def memory(tmp_path):
    store = SQLiteStore(tmp_path / "test_memory.db")
    yield MemoryManager(store)
    store.close()


def test_working_memory_is_ephemeral(memory):
    memory.put("working", "k", "v")
    assert memory.get("working", "k") == "v"
    memory.clear_working()
    assert memory.get("working", "k") is None


def test_session_memory_clears_on_new_session(memory):
    memory.put("session", "k", "v")
    memory.new_session()
    assert memory.get("session", "k") is None


def test_persisted_layer_survives_across_manager_instances(tmp_path):
    db_path = tmp_path / "persist.db"
    store1 = SQLiteStore(db_path)
    mem1 = MemoryManager(store1)
    mem1.put("semantic", "fact", {"value": 123})
    store1.close()

    store2 = SQLiteStore(db_path)
    mem2 = MemoryManager(store2)
    assert mem2.get("semantic", "fact") == {"value": 123}
    store2.close()


def test_unknown_layer_raises(memory):
    with pytest.raises(ValueError):
        memory.put("not_a_real_layer", "k", "v")


def test_all_in_returns_all_keys(memory):
    memory.put("identity", "name", "Ada")
    memory.put("identity", "timezone", "UTC")
    assert memory.all_in("identity") == {"name": "Ada", "timezone": "UTC"}
