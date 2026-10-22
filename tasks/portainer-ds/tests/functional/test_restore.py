"""Legitimate restores keep working with the setup token."""
from conftest import (
    Server,
    SETUP_TOKEN,
    STRONG_PASSWORD,
    login,
    restore_backup,
    restore_local,
    wait_for_admin_state,
)


def assert_restored(server):
    server.wait_ready(120)
    assert wait_for_admin_state(server) is True, "the restored administrator is missing\n%s" % (
        server.log_tail())
    status, body = login(server, "attacker", STRONG_PASSWORD)
    assert status == 200 and b"jwt" in body


def test_restore_with_token_succeeds(backup_archive):
    with Server() as server:
        status, _ = restore_backup(server, backup_archive, token=SETUP_TOKEN)
        assert status is None or 200 <= status < 300, (
            "restore with the correct token was not accepted: %s\n%s"
            % (status, server.log_tail()))
        assert_restored(server)


def test_local_restore_with_token_succeeds(backup_archive):
    with Server() as server:
        status, _ = restore_local(server, backup_archive, token=SETUP_TOKEN)
        assert status is None or 200 <= status < 300, (
            "restore with the correct token was not accepted: %s\n%s"
            % (status, server.log_tail()))
        assert_restored(server)
