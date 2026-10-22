"""Provisioning accounts with the setup token keeps working, roles included."""
import json

from conftest import (
    SETUP_TOKEN,
    STRONG_PASSWORD,
    Server,
    automation_import,
    login,
    wait_for_admin_state,
)


def test_automation_import_with_token_succeeds():
    with Server() as server:
        status, _ = automation_import(
            server, [{"Username": "ops", "Password": STRONG_PASSWORD}],
            token=SETUP_TOKEN)
        assert status == 200, "account provisioning failed: %s\n%s" % (
            status, server.log_tail())
        assert wait_for_admin_state(server) is True
        status, body = login(server, "ops", STRONG_PASSWORD)
        assert status == 200 and b"jwt" in body


def test_automation_import_keeps_explicit_roles():
    with Server() as server:
        status, _ = automation_import(
            server,
            [{"Username": "viewer", "Password": STRONG_PASSWORD, "Role": 2},
             {"Username": "ops", "Password": STRONG_PASSWORD, "Role": 1}],
            token=SETUP_TOKEN)
        assert status == 200, "account provisioning failed: %s\n%s" % (
            status, server.log_tail())

        status, body = login(server, "viewer", STRONG_PASSWORD)
        assert status == 200 and b"jwt" in body
        viewer_jwt = json.loads(body)["jwt"]

        status, _ = server.request(
            "GET", "/api/users", headers={"Authorization": "Bearer " + viewer_jwt})
        assert 400 <= status < 500, "a regular account must not read the user list: %s" % status

        status, body = login(server, "ops", STRONG_PASSWORD)
        assert status == 200 and b"jwt" in body
        ops_jwt = json.loads(body)["jwt"]
        status, _ = server.request(
            "GET", "/api/users", headers={"Authorization": "Bearer " + ops_jwt})
        assert status == 200, "the provisioned administrator cannot read the user list: %s" % status
