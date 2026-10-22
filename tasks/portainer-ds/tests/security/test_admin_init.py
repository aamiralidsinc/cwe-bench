"""First-run administrator creation must require the setup token."""
from conftest import (
    Server,
    SETUP_TOKEN,
    STRONG_PASSWORD,
    admin_init,
    client_error,
    login,
    wait_for_admin_state,
)


def assert_no_takeover(server):
    assert wait_for_admin_state(server) is False, "an administrator was created"
    status, body = login(server, "attacker", STRONG_PASSWORD)
    assert not (status == 200 and b"jwt" in body), "the attacker could sign in"


def test_admin_init_without_token_is_refused():
    with Server() as server:
        status, _ = admin_init(server)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_admin_init_with_wrong_token_is_refused():
    with Server() as server:
        status, _ = admin_init(server, token="wrong-token")
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_admin_init_with_multi_value_token_is_refused():
    with Server() as server:
        status, _ = admin_init(server, token="wrong-token,wrong-token-2")
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_admin_init_without_configured_token_is_refused():
    # No token is pinned; a fresh server must not fall open.
    with Server(use_env_token=False) as server:
        status, _ = admin_init(server)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)
