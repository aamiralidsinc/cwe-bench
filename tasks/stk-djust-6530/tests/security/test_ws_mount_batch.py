"""A refusal inside a multiplexed mount must keep the shared session honest.

The batch response may report the refused view as a redirect, but the refused
view must not become the session's event target, and the sibling views mounted
on the same session must keep serving their events.
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


def _targets(batch, key):
    return [entry.get("target_id") for entry in batch.get(key) or []]


@pytest.mark.django_db
async def test_batch_refused_view_is_not_the_event_target():
    """Public view first, refused view second: the refused view must not take over."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            batch = await harness.ws_mount_batch(
                communicator,
                [
                    harness.batch_entry(views.PublicView, "pub", "/public/"),
                    harness.batch_entry(views.LoginRequiredView, "secret", "/secret/"),
                ],
            )
            assert batch.get("type") == "mount_batch", batch
            assert "pub" in _targets(batch, "views"), batch
            assert "secret" in _targets(batch, "navigate"), batch
            await harness.ws_event_refused(communicator, "login_mutation", "login_mutation")
            await harness.ws_event_runs(communicator, "public_ping", "public_ping")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_batch_hook_refused_view_is_not_the_event_target():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            batch = await harness.ws_mount_batch(
                communicator,
                [
                    harness.batch_entry(views.PublicView, "pub", "/public/"),
                    harness.batch_entry(views.HookRedirectView, "hook", "/secret/"),
                ],
            )
            assert batch.get("type") == "mount_batch", batch
            assert "pub" in _targets(batch, "views"), batch
            assert "hook" in _targets(batch, "navigate"), batch
            await harness.ws_event_refused(communicator, "hook_mutation", "hook_mutation")
            await harness.ws_event_runs(communicator, "public_ping", "public_ping")
        finally:
            await harness.ws_close(communicator)
