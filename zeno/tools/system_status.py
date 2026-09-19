"""System status tool — real local machine stats via psutil, with simple threshold alerting."""

from __future__ import annotations

from typing import Any

import psutil


def get_system_status() -> dict[str, Any]:
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "boot_time": psutil.boot_time(),
    }


def check_thresholds(
    status: dict[str, Any],
    cpu_threshold: float = 90.0,
    memory_threshold: float = 90.0,
    disk_threshold: float = 95.0,
) -> list[str]:
    """Pure function: given a status dict (from get_system_status), return
    a list of human-readable alert strings for anything over threshold.
    Empty list means nothing is wrong — never fabricates an alert."""
    alerts = []
    if status["cpu_percent"] >= cpu_threshold:
        alerts.append(f"CPU usage high: {status['cpu_percent']}% (threshold {cpu_threshold}%)")
    if status["memory_percent"] >= memory_threshold:
        alerts.append(f"Memory usage high: {status['memory_percent']}% (threshold {memory_threshold}%)")
    if status["disk_percent"] >= disk_threshold:
        alerts.append(f"Disk usage high: {status['disk_percent']}% (threshold {disk_threshold}%)")
    return alerts

