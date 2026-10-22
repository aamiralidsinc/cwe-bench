"""An instance that loses its operator account returns to the protected setup state."""
from conftest import (
    ADMIN_PASSWORD_HASH,
    STRONG_PASSWORD,
    Server,
    admin_init,
    client_error,
    demote_operator,
    login,
    restore_backup,
    wait_for_admin_state,
)


def remove_operator_account(server):
    status = demote_operator(server)
    assert status == 200, "the operator account could not change role: %s" % status
    assert wait_for_admin_state(server) is False, "the instance still has an operator account"


def assert_no_takeover(server):
    assert wait_for_admin_state(server) is False, "an administrator was created"
    status, body = login(server, "attacker", STRONG_PASSWORD)
    assert not (status == 200 and b"jwt" in body), "the attacker could sign in"


def test_admin_init_after_operator_account_removed_is_refused():
    # This instance had an operator account when it started and lost it while running.
    # It has no operator account now, so a client that proves nothing must not create one.
    # No token is pinned, so the instance has to rely on the token it makes for itself.
    with Server(use_env_token=False, admin_password=ADMIN_PASSWORD_HASH) as server:
        remove_operator_account(server)
        status, _ = admin_init(server)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)


def test_restore_after_operator_account_removed_is_refused(backup_archive):
    # Replacing the persistent state is covered by the same rule: the instance has no
    # operator account at this moment, whatever it had when it started.
    with Server(use_env_token=False, admin_password=ADMIN_PASSWORD_HASH) as server:
        remove_operator_account(server)
        status, _ = restore_backup(server, backup_archive)
        assert client_error(status), "expected a client error, got %s" % status
        assert_no_takeover(server)
