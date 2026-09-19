"""
Weather tool — real HTTP call to the Open-Meteo API (no API key required).

The network call is isolated behind `fetch_fn` so tests can inject a fake
and verify the parsing logic without needing a live connection or secrets.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

_BASE_URL = "https://api.open-meteo.com/v1/forecast"

FetchFn = Callable[[str, dict[str, Any]], dict[str, Any]]


def _default_fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_current_weather(
    latitude: float,
    longitude: float,
    fetch_fn: FetchFn = _default_fetch,
) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
    }
    data = fetch_fn(_BASE_URL, params)
    current = data.get("current_weather")
    if not current:
        raise ValueError(f"Unexpected response shape from weather API: {data}")
    return {
        "temperature_c": current["temperature"],
        "windspeed_kmh": current["windspeed"],
        "weather_code": current["weathercode"],
        "observed_at": current["time"],
    }
