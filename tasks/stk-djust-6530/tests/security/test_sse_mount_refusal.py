"""Refused mounts on the streaming transport must not dispatch events either.

Each test mounts through the product's stream view, then posts an event through
the product's event view and requires a client error with no handler run.
"""

from __future__ import annotations

import pytest
from django.test import override_settings

from support import harness, views

pytestmark = pytest.mark.asyncio

SETTINGS = dict(ALLOWED_HOSTS=["*"], LIVEVIEW_ALLOWED_MODULES=[])


@pytest.fixture(autouse=True)
def _reset_handler_log():
    views.reset()
    yield
    views.reset()


async def _mount_expect_denial(view_class, user=None):
    session_id, session, _response = await harness.sse_mount(view_class, user=user)
    try:
        messages = harness.sse_messages(session)
        assert any(m.get("type") in ("navigate", "error") for m in messages), messages
        assert not any(m.get("type") == "mount" for m in messages), messages
        return session_id, session
    except Exception:
        harness.sse_forget(session_id)
        raise


async def _assert_event_refused(session_id, event_name):
    response = await harness.sse_event(session_id, event_name)
    assert response.status_code >= 400, (
        f"refused mount still accepted the event (status {response.status_code})"
    )
    assert event_name not in views.EXECUTED, f"refused mount dispatched {event_name!r}"


@pytest.mark.django_db
async def test_stream_login_required_mount_does_not_dispatch():
    with override_settings(**SETTINGS):
        session_id, _session = await _mount_expect_denial(views.LoginRequiredView)
        try:
            await _assert_event_refused(session_id, "login_mutation")
        finally:
            harness.sse_forget(session_id)


@pytest.mark.django_db
async def test_stream_permission_required_mount_does_not_dispatch():
    with override_settings(**SETTINGS):
        session_id, _session = await _mount_expect_denial(views.PermissionRequiredView)
        try:
            await _assert_event_refused(session_id, "perm_mutation")
        finally:
            harness.sse_forget(session_id)


@pytest.mark.django_db
async def test_stream_permission_denied_mount_does_not_dispatch():
    """A signed-in user without the declared permission is refused."""
    with override_settings(**SETTINGS):
        session_id, _session = await _mount_expect_denial(
            views.PermissionRequiredView, user=views.UnprivilegedUser()
        )
        try:
            await _assert_event_refused(session_id, "perm_mutation")
        finally:
            harness.sse_forget(session_id)


@pytest.mark.django_db
async def test_stream_developer_predicate_refusal_does_not_dispatch():
    with override_settings(**SETTINGS):
        session_id, _session = await _mount_expect_denial(views.CheckPermissionsDeniedView)
        try:
            await _assert_event_refused(session_id, "checkperm_mutation")
        finally:
            harness.sse_forget(session_id)
