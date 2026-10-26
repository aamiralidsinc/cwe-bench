"""A refused WebSocket mount must not leave a session able to run the view.

Every test drives the product's WebSocket consumer with its real frame protocol:
connect, mount (or live-redirect-mount), then dispatch an event and require that
the refused view's handler did not run.
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
async def test_login_required_mount_does_not_dispatch():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            first = await harness.ws_mount(communicator, views.LoginRequiredView)
            assert first.get("type") == "navigate", first
            await harness.ws_event_refused(communicator, "login_mutation", "login_mutation")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_permission_required_mount_does_not_dispatch():
    """An anonymous client on a permission-gated view is redirected, then cut off."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            first = await harness.ws_mount(communicator, views.PermissionRequiredView)
            assert first.get("type") == "navigate", first
            await harness.ws_event_refused(communicator, "perm_mutation", "perm_mutation")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_developer_predicate_refusal_does_not_dispatch():
    """The view's own authorization predicate refused the mount."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            first = await harness.ws_mount(communicator, views.CheckPermissionsDeniedView)
            assert first.get("type") == "navigate", first
            await harness.ws_event_refused(
                communicator, "checkperm_mutation", "checkperm_mutation"
            )
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_remount_on_open_session_does_not_dispatch():
    """A refused re-mount on an already-open session must not keep the view live."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            mounted = await harness.ws_mount(communicator, views.PublicView, url="/public/")
            assert mounted.get("type") == "mount", mounted
            redirect = await harness.ws_live_redirect_mount(
                communicator, views.LoginRequiredView, url="/secret/"
            )
            assert redirect.get("type") == "navigate", redirect
            await harness.ws_event_refused(communicator, "login_mutation", "login_mutation")
        finally:
            await harness.ws_close(communicator)
