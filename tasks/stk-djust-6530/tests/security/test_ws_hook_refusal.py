"""A mount-time hook that redirects must not leave the view dispatchable."""

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
async def test_hook_redirect_mount_does_not_dispatch():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            first = await harness.ws_mount(communicator, views.HookRedirectView)
            assert first.get("type") == "navigate", first
            await harness.ws_event_refused(communicator, "hook_mutation", "hook_mutation")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_decorated_hook_redirect_mount_does_not_dispatch():
    """The same hook written with the product's public decorator."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            first = await harness.ws_mount(communicator, views.DecoratedHookRedirectView)
            assert first.get("type") == "navigate", first
            await harness.ws_event_refused(
                communicator, "decorated_hook_mutation", "decorated_hook_mutation"
            )
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_hook_redirect_on_remount_does_not_dispatch():
    """A hook redirect during a client-side re-mount on an open session."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            mounted = await harness.ws_mount(communicator, views.PublicView, url="/public/")
            assert mounted.get("type") == "mount", mounted
            redirect = await harness.ws_live_redirect_mount(
                communicator, views.HookRedirectView, url="/secret/"
            )
            assert redirect.get("type") == "navigate", redirect
            await harness.ws_event_refused(communicator, "hook_mutation", "hook_mutation")
        finally:
            await harness.ws_close(communicator)
