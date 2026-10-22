"""The legitimate first-run flow keeps working with the setup token."""
import json

from conftest import (
    Server,
    SETUP_TOKEN,
    STRONG_PASSWORD,
    admin_init,
    login,
    wait_for_admin_state,
)


def test_first_run_admin_init_with_token_succeeds():
    with Server() as server:
        status, _ = admin_init(server, token=SETUP_TOKEN)
        assert status == 200, "first-run administrator creation failed: %s\n%s" % (
            status, server.log_tail())
        assert wait_for_admin_state(server) is True
        status, body = login(server, "attacker", STRONG_PASSWORD)
        assert status == 200 and b"jwt" in body


def test_first_run_validation_is_unchanged():
    with Server() as server:
        status, _ = server.post_json(
            "/api/users/admin/init",
            {"Username": "attacker", "Password": "short"},
            headers={"X-Setup-Token": SETUP_TOKEN},
        )
        assert status == 400, "a weak password must still be refused: %s" % status
        assert wait_for_admin_state(server) is False

        status, _ = server.request(
            "POST", "/api/users/admin/init", b"{not json",
            {"Content-Type": "application/json", "X-Setup-Token": SETUP_TOKEN},
        )
        assert status == 400, "a malformed payload must still be refused: %s" % status

        status, _ = admin_init(server, token=SETUP_TOKEN)
        assert status == 200

        status, _ = admin_init(server, token=SETUP_TOKEN)
        assert status == 409, "a second initialization must still conflict: %s" % status


def test_public_settings_stays_public():
    with Server() as server:
        status, body = server.request("GET", "/api/settings/public")
        assert status == 200
        parsed = json.loads(body)
        assert isinstance(parsed, dict)
