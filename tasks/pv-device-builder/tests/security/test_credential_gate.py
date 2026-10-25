"""Security checks: a configured credential pair must gate every surface.

Each check starts the real command-line entry point and drives the port it
binds.  A check fails when dashboard-managed data reaches an unauthenticated
client (or when an unconfigured half-pair leaves the dashboard serving).
"""

from __future__ import annotations

import json

from dashboard_harness import DEVICE_MARKER, DEVICE_NAME, Dashboard, reached_inventory

CURRENT = {"ESPHOME_USERNAME": "admin", "ESPHOME_PASSWORD": "hunter2"}
LEGACY = {"USERNAME": "jesse", "PASSWORD": "shellsecret"}


def test_legacy_credential_pair_requires_authentication(tmp_path):
    """An operator's pre-rename pair must put the login gate in front of the inventory."""
    dash = Dashboard(tmp_path / "d", env=LEGACY).start()
    try:
        assert dash.wait_ready(), f"dashboard did not start: {dash.output[-2000:]}"
        status, body = dash.http("/devices")
        assert not reached_inventory(status, body), (
            f"device inventory served without credentials (status {status})"
        )
    finally:
        dash.stop()


def test_legacy_credential_pair_rejects_wrong_password(tmp_path):
    """The gate enabled by the pre-rename pair must actually check the secret."""
    dash = Dashboard(tmp_path / "d", env=LEGACY).start()
    try:
        assert dash.wait_ready(), f"dashboard did not start: {dash.output[-2000:]}"
        status, body = dash.http("/devices", auth=("jesse", "not-the-secret"))
        assert not reached_inventory(status, body), (
            f"wrong password accepted (status {status})"
        )
        status, body = dash.http("/devices", auth=("jesse", "shellsecret"))
        assert reached_inventory(status, body), (
            f"the configured credentials were refused (status {status})"
        )
    finally:
        dash.stop()


def test_lone_legacy_password_never_serves_open(tmp_path):
    """A password with no user name must stop startup, not serve unprotected."""
    dash = Dashboard(tmp_path / "d", env={"PASSWORD": "shellsecret"}).start()
    try:
        ready = dash.wait_ready(timeout=60)
        if not ready:
            assert dash.proc is not None
            assert dash.proc.poll() is not None, "dashboard neither started nor exited"
            assert dash.proc.returncode != 0, "half-configured credentials exited successfully"
            return
        status, body = dash.http("/devices")
        assert not reached_inventory(status, body), (
            f"dashboard served unprotected with only half a pair (status {status})"
        )
    finally:
        dash.stop()


def test_preauth_command_does_not_expose_inventory(tmp_path):
    """No unauthenticated client may read the managed inventory over the socket API."""
    dash = Dashboard(tmp_path / "d", env=CURRENT).start()
    try:
        assert dash.wait_ready(), f"dashboard did not start: {dash.output[-2000:]}"
        frames = dash.ws_exchange(
            [{"command": "dashboard/summary", "message_id": "m1", "args": {}}]
        )
        info, reply = frames[0], frames[1]
        assert info.get("requires_auth") is True
        payload = json.dumps(reply)
        assert DEVICE_NAME not in payload, f"inventory served before authentication: {payload[:400]}"
        assert reply.get("result") is None, f"command answered before authentication: {payload[:400]}"
    finally:
        dash.stop()


def test_public_export_requires_authentication(tmp_path):
    """No unauthenticated client may download a managed device configuration."""
    dash = Dashboard(tmp_path / "d", env=CURRENT).start()
    try:
        assert dash.wait_ready(), f"dashboard did not start: {dash.output[-2000:]}"
        status, body = dash.http(f"/api/config/export/{DEVICE_NAME}.yaml")
        assert not (200 <= status < 300), f"configuration download served without credentials (status {status})"
        assert DEVICE_MARKER not in body, "configuration body served without credentials"
    finally:
        dash.stop()
