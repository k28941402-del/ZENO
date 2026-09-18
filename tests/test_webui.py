import pytest

from zeno.webui import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.testing = True
    with app.test_client() as c:
        yield c


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ZENO" in resp.data


def test_status_reports_real_counts(client):
    resp = client.get("/api/status")
    data = resp.get_json()
    assert data["implemented"] > 0
    assert data["stub"] > 0
    assert data["pending_goals"] == 0


def test_tools_list_matches_registry_shape(client):
    resp = client.get("/api/tools")
    data = resp.get_json()
    assert any(t["name"] == "notes.create" for t in data)
    assert all(t["status"] in ("implemented", "stub") for t in data)


def test_turn_executes_a_real_tool(client):
    resp = client.post("/api/turn", json={"text": "note: buy milk"})
    data = resp.get_json()
    assert data["tool"] == "notes.create"
    assert data["output"]["title"] == "buy milk"


def test_turn_requires_text(client):
    resp = client.post("/api/turn", json={})
    assert resp.status_code == 400


def test_run_all_pending_end_to_end(client):
    delegate_resp = client.post("/api/delegate", json={"text": "note: from web ui"})
    goal = delegate_resp.get_json()
    assert goal["status"] == "pending"

    goals_resp = client.get("/api/goals")
    assert any(g["id"] == goal["id"] for g in goals_resp.get_json())

    run_resp = client.post("/api/run_pending")
    results = run_resp.get_json()
    assert len(results) == 1
    assert results[0]["handled"] is True
    assert results[0]["output"]["title"] == "from web ui"

    status_resp = client.get("/api/status")
    assert status_resp.get_json()["pending_goals"] == 0


def test_overview_returns_real_system_stats_and_empty_lists_initially(client):
    resp = client.get("/api/overview")
    data = resp.get_json()
    assert "cpu_percent" in data["system"]
    assert data["due_reminders"] == []
    assert data["notes"] == []
    assert data["projects"] == []


def test_overview_reflects_real_notes_and_reminders(client):
    client.post("/api/turn", json={"text": "note: dashboard test"})
    resp = client.get("/api/overview")
    data = resp.get_json()
    assert len(data["notes"]) == 1
    assert data["notes"][0]["title"] == "dashboard test"


def test_history_reflects_real_turns(client):
    client.post("/api/turn", json={"text": "note: history test"})
    resp = client.get("/api/history")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["tool"] == "notes.create"
    assert "timestamp" in data[0]


def test_weather_requires_coordinates(client):
    resp = client.post("/api/weather", json={})
    assert resp.status_code == 400


def test_weather_returns_real_tool_output_with_injected_fetch(client, monkeypatch):
    import zeno.tools.weather as weather_module

    def fake_get(url, params, timeout):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"current_weather": {"temperature": 21.5, "windspeed": 4.0, "weathercode": 1, "time": "now"}}

        return FakeResponse()

    monkeypatch.setattr(weather_module.requests, "get", fake_get)
    resp = client.post("/api/weather", json={"latitude": 23.6, "longitude": 58.5})
    data = resp.get_json()
    assert data["temperature_c"] == 21.5


def test_godseye_status_is_honest_when_nothing_is_running(client):
    # Nothing is listening on 4173 in the test environment — this must
    # report False, not fabricate a "connected" state.
    resp = client.get("/api/godseye/status")
    data = resp.get_json()
    assert data["connected"] is False
    assert "4173" in data["url"]
