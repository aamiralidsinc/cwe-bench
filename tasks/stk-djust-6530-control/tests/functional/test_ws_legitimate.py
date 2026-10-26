"""Legitimate WebSocket mounts must keep working exactly as today."""

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
async def test_public_view_mounts_and_dispatches():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            mounted = await harness.ws_mount(communicator, views.PublicView)
            assert mounted.get("type") == "mount", mounted
            await harness.ws_event_runs(communicator, "public_ping", "public_ping")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_authenticated_user_mounts_login_required_view():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect(user=views.AuthenticatedUser())
        try:
            mounted = await harness.ws_mount(communicator, views.LoginRequiredView)
            assert mounted.get("type") == "mount", mounted
            await harness.ws_event_runs(communicator, "login_mutation", "login_mutation")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_authorized_permission_required_view_mounts():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect(user=views.AuthenticatedUser())
        try:
            mounted = await harness.ws_mount(communicator, views.PermissionRequiredView)
            assert mounted.get("type") == "mount", mounted
            await harness.ws_event_runs(communicator, "perm_mutation", "perm_mutation")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_hook_that_does_not_redirect_mounts():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            mounted = await harness.ws_mount(communicator, views.HookAllowedView)
            assert mounted.get("type") == "mount", mounted
            await harness.ws_event_runs(communicator, "hookok_ping", "hookok_ping")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_client_side_navigation_to_a_public_view_mounts():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            first = await harness.ws_mount(communicator, views.PublicView, url="/public/")
            assert first.get("type") == "mount", first
            moved = await harness.ws_live_redirect_mount(
                communicator, views.PublicDetailView, url="/other/"
            )
            assert moved.get("type") == "mount", moved
            await harness.ws_event_runs(communicator, "other_ping", "other_ping")
        finally:
            await harness.ws_close(communicator)
