from zeno.tools.system_status import get_system_status


def test_system_status_returns_expected_keys():
    status = get_system_status()
    assert set(status.keys()) == {"cpu_percent", "memory_percent", "disk_percent", "boot_time"}
    assert 0 <= status["cpu_percent"] <= 100
    assert 0 <= status["memory_percent"] <= 100
