"""The deprecated bootstrap API must require the setup token as well."""
from conftest import (
    Server,
    STRONG_PASSWORD,
    client_error,
    legacy_admin_init,
    login,
    wait_for_admin_state,
)


def assert_no_takeover(server):
    assert wait_for_admin_state(server) is False, "an administrator was created"
    status, body = login(server, "attacker", STRONG_PASSWORD)
    assert not (status == 200 and b"jwt" in body), "the attacker could sign in"


def test_legacy_admin_init_without_token_is_refused():
    with Server() as server:
        status, _ = legacy_admin_init(server)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_legacy_admin_init_with_wrong_token_is_refused():
    with Server() as server:
        status, _ = legacy_admin_init(server, token="wrong-token")
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)
