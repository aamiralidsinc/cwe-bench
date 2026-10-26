"""Legitimate streaming-transport mounts must keep working exactly as today."""

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


async def _mount_and_dispatch(view_class, event_name, user=None):
    session_id, session, _response = await harness.sse_mount(view_class, user=user)
    try:
        messages = harness.sse_messages(session)
        assert any(m.get("type") == "mount" for m in messages), messages
        response = await harness.sse_event(session_id, event_name)
        assert response.status_code == 200, (
            f"legitimate event was refused (status {response.status_code})"
        )
        assert event_name in views.EXECUTED, f"legitimate mount did not dispatch {event_name!r}"
    finally:
        harness.sse_forget(session_id)


@pytest.mark.django_db
async def test_public_view_mounts_and_dispatches():
    with override_settings(**SETTINGS):
        await _mount_and_dispatch(views.PublicView, "public_ping")


@pytest.mark.django_db
async def test_authenticated_user_mounts_login_required_view():
    with override_settings(**SETTINGS):
        await _mount_and_dispatch(
            views.LoginRequiredView, "login_mutation", user=views.AuthenticatedUser()
        )


@pytest.mark.django_db
async def test_authorized_permission_required_view_mounts():
    with override_settings(**SETTINGS):
        await _mount_and_dispatch(
            views.PermissionRequiredView, "perm_mutation", user=views.AuthenticatedUser()
        )


@pytest.mark.django_db
async def test_developer_predicate_that_allows_mounts():
    with override_settings(**SETTINGS):
        await _mount_and_dispatch(views.CheckPermissionsAllowedView, "checkpermok_ping")


@pytest.mark.django_db
async def test_refusal_is_reported_to_the_client():
    """A refused mount is still reported as a redirect the client can follow."""
    with override_settings(**SETTINGS):
        session_id, session, _response = await harness.sse_mount(views.LoginRequiredView)
        try:
            messages = harness.sse_messages(session)
            redirects = [m for m in messages if m.get("type") == "navigate"]
            assert redirects, f"refusal was not reported to the client: {messages!r}"
            assert redirects[0].get("to") == "/accounts/login/", redirects[0]
        finally:
            harness.sse_forget(session_id)
