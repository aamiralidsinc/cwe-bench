"""Fixtures shared by the behavioural suites (copied into the workspace at grade time)."""

import pytest

from support import CSRF_TOKEN


@pytest.fixture
def login(test_client):
    """Log a user in through the session and return a matching CSRF token."""
    def _login(user):
        with test_client.session_transaction() as sess:
            sess.set_session_user(user)
            sess['_csrf_token'] = CSRF_TOKEN
        return CSRF_TOKEN
    return _login
