import pytest

from zeno.tools.weather import get_current_weather


def fake_fetch(url, params):
    return {
        "current_weather": {
            "temperature": 21.5,
            "windspeed": 10.2,
            "weathercode": 3,
            "time": "2026-01-01T12:00",
        }
    }


def broken_fetch(url, params):
    return {"unexpected": "shape"}


def test_get_current_weather_parses_response():
    result = get_current_weather(51.5, -0.1, fetch_fn=fake_fetch)
    assert result["temperature_c"] == 21.5
    assert result["windspeed_kmh"] == 10.2


def test_get_current_weather_raises_on_bad_shape():
    with pytest.raises(ValueError):
        get_current_weather(0, 0, fetch_fn=broken_fetch)
