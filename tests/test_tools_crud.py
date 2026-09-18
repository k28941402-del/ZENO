import pytest

from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore
from zeno.tools import notes, projects, reminders


@pytest.fixture
def memory(tmp_path):
    store = SQLiteStore(tmp_path / "crud.db")
    yield MemoryManager(store)
    store.close()


def test_notes_create_list_delete(memory):
    note = notes.create_note(memory, "Groceries", "milk, eggs")
    assert note["title"] == "Groceries"
    assert len(notes.list_notes(memory)) == 1
    assert notes.delete_note(memory, note["id"]) is True
    assert notes.list_notes(memory) == []


def test_reminders_due_filtering(memory):
    reminders.create_reminder(memory, "past due", "2020-01-01T00:00:00")
    reminders.create_reminder(memory, "far future", "2999-01-01T00:00:00")
    due = reminders.list_due(memory, as_of_iso="2024-01-01T00:00:00")
    assert len(due) == 1
    assert due[0]["text"] == "past due"


def test_reminders_complete_excludes_from_due(memory):
    r = reminders.create_reminder(memory, "task", "2020-01-01T00:00:00")
    reminders.complete_reminder(memory, r["id"])
    assert reminders.list_due(memory, as_of_iso="2024-01-01T00:00:00") == []


def test_projects_status_lifecycle(memory):
    p = projects.create_project(memory, "ZENO")
    assert p["status"] == "active"
    projects.set_status(memory, p["id"], "paused")
    assert projects.list_projects(memory, status="paused")[0]["id"] == p["id"]


def test_projects_invalid_status_raises(memory):
    p = projects.create_project(memory, "X")
    with pytest.raises(ValueError):
        projects.set_status(memory, p["id"], "not_a_status")
