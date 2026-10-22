"""Restoring a database on a fresh instance must require the setup token."""
from conftest import (
    Server,
    STRONG_PASSWORD,
    client_error,
    login,
    restore_backup,
    restore_local,
    wait_for_admin_state,
)


def assert_no_takeover(server):
    assert wait_for_admin_state(server) is False, "the restored database took effect"
    status, body = login(server, "attacker", STRONG_PASSWORD)
    assert not (status == 200 and b"jwt" in body), "the attacker could sign in"


def test_restore_without_token_is_refused(backup_archive):
    with Server() as server:
        status, _ = restore_backup(server, backup_archive)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_restore_with_wrong_token_is_refused(backup_archive):
    with Server() as server:
        status, _ = restore_backup(server, backup_archive, token="wrong-token")
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_local_restore_without_token_is_refused(backup_archive):
    with Server() as server:
        status, _ = restore_local(server, backup_archive)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_local_restore_with_wrong_token_is_refused(backup_archive):
    with Server() as server:
        status, _ = restore_local(server, backup_archive, token="wrong-token")
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)
