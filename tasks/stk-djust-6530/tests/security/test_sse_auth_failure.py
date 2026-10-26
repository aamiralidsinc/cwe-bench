"""When the authorization check cannot decide, the mount must be refused.

The view's own predicate raises; the stream must report the refusal and must not
leave a live session able to run the view's handler.
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


@pytest.mark.django_db
async def test_failed_authorization_check_does_not_mount_or_dispatch():
    with override_settings(**SETTINGS):
        session_id, session, _response = await harness.sse_mount(views.CheckPermissionsCrashesView)
        try:
            messages = harness.sse_messages(session)
            assert not any(m.get("type") == "mount" for m in messages), (
                f"an undecidable authorization check let the view mount: {messages!r}"
            )
            response = await harness.sse_event(session_id, "crash_mutation")
            assert response.status_code >= 400, (
                f"undecidable authorization check still accepted an event "
                f"(status {response.status_code})"
            )
            assert "crash_mutation" not in views.EXECUTED, (
                "an undecidable authorization check still dispatched the handler"
            )
        finally:
            harness.sse_forget(session_id)


@pytest.mark.django_db
async def test_failed_authorization_check_leaves_no_event_route():
    """The same refusal must hold when the permission backend itself fails."""
    with override_settings(**SETTINGS):
        session_id, session, _response = await harness.sse_mount(
            views.PermissionRequiredView, user=views.BrokenAuthBackendUser()
        )
        try:
            messages = harness.sse_messages(session)
            assert not any(m.get("type") == "mount" for m in messages), (
                f"a failed permission backend let the view mount: {messages!r}"
            )
            response = await harness.sse_event(session_id, "perm_mutation")
            assert response.status_code >= 400, (
                f"a failed permission backend still accepted an event "
                f"(status {response.status_code})"
            )
            assert "perm_mutation" not in views.EXECUTED, (
                "a failed permission backend still dispatched the handler"
            )
        finally:
            harness.sse_forget(session_id)
