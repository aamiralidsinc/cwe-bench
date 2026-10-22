"""Behaviour on an instance that already has an administrator is unchanged."""
from conftest import (
    ADMIN_PASSWORD_HASH,
    SETUP_TOKEN,
    STRONG_PASSWORD,
    Server,
    admin_init,
    demote_operator,
    legacy_admin_init,
    login,
    restore_backup,
    restore_local,
)


def test_restart_with_existing_admin_needs_no_token():
    first = Server()
    try:
        status, _ = admin_init(first, token=SETUP_TOKEN)
        assert status == 200
    finally:
        first.stop()

    # The same data directory, now with an administrator, started without a pinned token.
    with Server(use_env_token=False, data_dir=first.data) as server:
        status, _ = admin_init(server)
        assert status == 409, "administrator init must still conflict: %s" % status

        status, _ = legacy_admin_init(server)
        assert status == 409, "administrator init must still conflict: %s" % status

        status, _ = restore_backup(server, b"not a backup archive")
        assert status == 400, "restore on an initialized instance must still be refused: %s" % status

        status, _ = restore_local(server, b"not a backup archive")
        assert status == 400, "restore on an initialized instance must still be refused: %s" % status


def test_admin_password_startup_needs_no_token():
    with Server(use_env_token=False, admin_password=ADMIN_PASSWORD_HASH) as server:
        status, _ = login(server, "admin", STRONG_PASSWORD)
        assert status == 200, "the administrator from the startup flag cannot sign in: %s" % status

        status, _ = admin_init(server)
        assert status == 409, "administrator init must still conflict: %s" % status

        status, _ = restore_backup(server, b"not a backup archive")
        assert status == 400, "restore on an initialized instance must still be refused: %s" % status


def test_operator_account_change_keeps_instance_usable():
    """The operator can still change their own account, and the instance keeps serving."""
    with Server(use_env_token=False, admin_password=ADMIN_PASSWORD_HASH) as server:
        # While the operator account exists the initialization actions keep their
        # present answers without a token.
        status, _ = admin_init(server)
        assert status == 409, "administrator init must still conflict: %s" % status
        status, _ = restore_backup(server, b"not a backup archive")
        assert status == 400, "restore must still be refused on an initialized instance: %s" % status

        status = demote_operator(server)
        assert status == 200, "the operator account could not change role: %s" % status

        status, body = login(server, "admin", STRONG_PASSWORD)
        assert status == 200 and b"jwt" in body, "the changed account cannot sign in: %s" % status
        status, _ = server.request("GET", "/api/system/status")
        assert status == 200
