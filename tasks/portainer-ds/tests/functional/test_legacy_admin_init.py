"""The deprecated bootstrap API keeps working with the setup token."""
from conftest import (
    SETUP_TOKEN,
    STRONG_PASSWORD,
    Server,
    legacy_admin_init,
    login,
)


def test_legacy_admin_init_with_token_succeeds():
    with Server() as server:
        status, _ = legacy_admin_init(server, token=SETUP_TOKEN)
        assert status == 200, "first-run administrator creation failed: %s\n%s" % (
            status, server.log_tail())
        status, body = login(server, "attacker", STRONG_PASSWORD)
        assert status == 200 and b"jwt" in body
