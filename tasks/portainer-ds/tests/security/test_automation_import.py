"""Provisioning accounts on a fresh instance must require the setup token."""
from conftest import (
    Server,
    STRONG_PASSWORD,
    automation_import,
    client_error,
    login,
    wait_for_admin_state,
)


def assert_no_takeover(server):
    assert wait_for_admin_state(server) is False, "an administrator was created"
    status, body = login(server, "attacker", STRONG_PASSWORD)
    assert not (status == 200 and b"jwt" in body), "the attacker could sign in"


def test_automation_import_without_token_is_refused():
    with Server() as server:
        status, _ = automation_import(
            server, [{"Username": "attacker", "Password": STRONG_PASSWORD}])
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_automation_import_with_wrong_token_is_refused():
    with Server() as server:
        status, _ = automation_import(
            server, [{"Username": "attacker", "Password": STRONG_PASSWORD}],
            token="wrong-token")
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)
