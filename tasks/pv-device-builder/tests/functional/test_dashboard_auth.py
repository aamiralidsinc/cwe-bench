"""Functional checks: legitimate configurations and authenticated use keep working."""

from __future__ import annotations

import json

from dashboard_harness import DEVICE_MARKER, DEVICE_NAME, Dashboard, reached_inventory

CURRENT = {"ESPHOME_USERNAME": "admin", "ESPHOME_PASSWORD": "hunter2"}
LEGACY = {"USERNAME": "jesse", "PASSWORD": "shellsecret"}


def _ready(dash):
    assert dash.wait_ready(), f"dashboard did not start: {dash.output[-2000:]}"
    return dash


def test_starts_open_without_credentials(tmp_path):
    """No credential configuration keeps the dashboard usable, exactly as today."""
    dash = Dashboard(tmp_path / "d").start()
    try:
        _ready(dash)
        status, body = dash.http("/devices")
        assert reached_inventory(status, body)
    finally:
        dash.stop()


def test_lone_os_username_is_not_a_credential(tmp_path):
    """A user name exported by the login shell alone neither gates nor blocks startup."""
    dash = Dashboard(tmp_path / "d", env={"USERNAME": "jesse"}).start()
    try:
        _ready(dash)
        status, body = dash.http("/devices")
        assert reached_inventory(status, body), (
            f"a lone OS user name changed startup behaviour (status {status})"
        )
    finally:
        dash.stop()


def test_current_pair_authenticates(tmp_path):
    """The current environment pair still gates the inventory and accepts its values."""
    dash = Dashboard(tmp_path / "d", env=CURRENT).start()
    try:
        _ready(dash)
        status, body = dash.http("/devices")
        assert not reached_inventory(status, body)
        status, body = dash.http("/devices", auth=("admin", "hunter2"))
        assert reached_inventory(status, body)
    finally:
        dash.stop()


def test_current_pair_beats_legacy_pair(tmp_path):
    """When both pairs are present the current one decides; stale values do not authenticate."""
    dash = Dashboard(tmp_path / "d", env={**LEGACY, **CURRENT}).start()
    try:
        _ready(dash)
        status, body = dash.http("/devices", auth=("admin", "hunter2"))
        assert reached_inventory(status, body)
        status, body = dash.http("/devices", auth=("jesse", "shellsecret"))
        assert not reached_inventory(status, body), "the stale pair still authenticated"
    finally:
        dash.stop()


def test_cli_flags_beat_legacy_pair(tmp_path):
    """Command-line flags keep precedence over the pre-rename pair."""
    dash = Dashboard(tmp_path / "d", env=LEGACY,
                     args=("--username", "cli", "--password", "clipass")).start()
    try:
        _ready(dash)
        status, body = dash.http("/devices", auth=("cli", "clipass"))
        assert reached_inventory(status, body)
        status, body = dash.http("/devices", auth=("jesse", "shellsecret"))
        assert not reached_inventory(status, body), "the pre-rename pair overrode the flags"
    finally:
        dash.stop()


def test_half_current_pair_stops_startup(tmp_path):
    """Half of the current pair is still a configuration error, not an open dashboard."""
    dash = Dashboard(tmp_path / "d", env={"ESPHOME_USERNAME": "admin"}).start()
    try:
        ready = dash.wait_ready(timeout=60)
        assert not ready, "dashboard started with half a credential pair"
        assert dash.proc is not None and dash.proc.poll() is not None
        assert dash.proc.returncode != 0
    finally:
        dash.stop()


def test_os_username_is_not_promoted(tmp_path):
    """The OS user name must not fill the missing half of a current-scheme pair."""
    dash = Dashboard(tmp_path / "d",
                     env={"USERNAME": "osuser", "ESPHOME_PASSWORD": "hunter2"}).start()
    try:
        if not dash.wait_ready(timeout=60):
            assert dash.proc is not None and dash.proc.poll() is not None
            assert dash.proc.returncode != 0
            return
        status, body = dash.http("/devices", auth=("osuser", "hunter2"))
        assert not reached_inventory(status, body), "the OS user name was promoted to a credential"
    finally:
        dash.stop()


def test_authenticated_client_can_read_summary(tmp_path):
    """After signing in, the instance summary still answers with the managed devices."""
    dash = Dashboard(tmp_path / "d", env=CURRENT).start()
    try:
        _ready(dash)
        frames = dash.ws_exchange(
            [
                {"command": "auth/login", "message_id": "m1",
                 "args": {"username": "admin", "password": "hunter2"}},
                {"command": "dashboard/summary", "message_id": "m2", "args": {}},
            ]
        )
        assert frames[1].get("result", {}).get("token")
        summary = frames[2].get("result")
        assert summary is not None, f"summary refused for an authenticated client: {frames[2]}"
        assert DEVICE_NAME in json.dumps(summary)
    finally:
        dash.stop()


def test_authenticated_client_can_download_configuration(tmp_path):
    """An authenticated request still downloads the configuration file."""
    dash = Dashboard(tmp_path / "d", env=CURRENT).start()
    try:
        _ready(dash)
        status, body = dash.http(
            f"/api/config/export/{DEVICE_NAME}.yaml", auth=("admin", "hunter2")
        )
        assert 200 <= status < 300, f"authenticated download refused (status {status})"
        assert DEVICE_MARKER in body
    finally:
        dash.stop()
