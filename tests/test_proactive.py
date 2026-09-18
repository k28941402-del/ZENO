from datetime import datetime, timedelta

import pytest

from zeno.memory.layers import MemoryManager
from zeno.memory.store import SQLiteStore
from zeno.tools import reminders
from zeno.tools.proactive import build_morning_briefing, check_idle


@pytest.fixture
def memory(tmp_path):
    store = SQLiteStore(tmp_path / "proactive.db")
    yield MemoryManager(store)
    store.close()


def fake_weather(lat, lon):
    return {"temperature_c": 15.0, "windspeed_kmh": 5.0, "weather_code": 1, "observed_at": "now"}


def test_briefing_includes_due_reminders(memory):
    reminders.create_reminder(memory, "walk the dog", "2020-01-01T00:00:00")
    briefing = build_morning_briefing(memory)
    assert len(briefing["due_reminders"]) == 1
    assert briefing["weather"] is None


def test_briefing_includes_weather_when_coords_given(memory):
    briefing = build_morning_briefing(memory, latitude=1.0, longitude=2.0, weather_fn=fake_weather)
    assert briefing["weather"]["temperature_c"] == 15.0


def test_briefing_omits_weather_without_coords(memory):
    briefing = build_morning_briefing(memory)
    assert briefing["weather"] is None


def test_check_idle_true_after_threshold():
    last = datetime(2026, 1, 1, 9, 0, 0)  # noqa: DTZ001 — naive by design, matches check_idle's naive contract
    now = last + timedelta(minutes=20)
    assert check_idle(last, now, threshold_minutes=15) is True


def test_check_idle_false_before_threshold():
    last = datetime(2026, 1, 1, 9, 0, 0)  # noqa: DTZ001 — naive by design, matches check_idle's naive contract
    now = last + timedelta(minutes=5)
    assert check_idle(last, now, threshold_minutes=15) is False
