"""Alert thresholds keep their values and JSON types."""

import requests


def test_all_limits_keep_thresholds(api):
    r = requests.get(api + "/all/limits", timeout=10)
    assert r.status_code == 200, r.text
    limits = r.json()
    assert limits["cpu"]["cpu_user_careful"] == 50.0
    assert limits["cpu"]["cpu_user_warning"] == 70.0
    assert limits["cpu"]["cpu_user_critical"] == 90.0
    assert limits["load"]["load_user_careful"] == 2.0
    assert limits["sensors"]["sensors_temperature_hdd_careful"] == 45.0
    assert limits["memswap"]["memswap_careful"] == 50.0
    assert isinstance(limits["cpu"]["history_size"], (int, float))


def test_plugin_limits_keep_thresholds(api):
    r = requests.get(api + "/cpu/limits", timeout=10)
    assert r.status_code == 200, r.text
    limits = r.json()
    assert limits["cpu_user_careful"] == 50.0
    assert isinstance(limits["history_size"], (int, float))
