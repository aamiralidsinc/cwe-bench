"""Mounting several views together must keep working exactly as today.

These are the coupled behaviours of the batch path: the redirect stays in the
batch's navigate list, and the sibling views mounted on the same shared session
keep mounting and keep serving their events.
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
async def test_batch_reports_redirect_and_keeps_siblings_serving():
    """A refused view first, a public sibling second: both outcomes are reported."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            batch = await harness.ws_mount_batch(
                communicator,
                [
                    harness.batch_entry(views.LoginRequiredView, "secret", "/secret/"),
                    harness.batch_entry(views.PublicView, "pub", "/public/"),
                ],
            )
            assert batch.get("type") == "mount_batch", batch
            assert "pub" in _targets(batch, "views"), batch
            assert "secret" in _targets(batch, "navigate"), batch
            await harness.ws_event_runs(communicator, "public_ping", "public_ping")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_batch_navigate_entry_carries_the_client_contract():
    """The client associates the redirect with the lazy element it asked for."""
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
            redirects = {entry.get("target_id"): entry for entry in batch.get("navigate") or []}
            assert "secret" in redirects, batch
            entry = redirects["secret"]
            assert entry.get("type") == "navigate", entry
            assert entry.get("to") == "/accounts/login/", entry
            assert entry.get("view", "").endswith("LoginRequiredView"), entry
            assert "pub" in _targets(batch, "views"), batch
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_batch_refusal_does_not_terminate_the_shared_socket():
    """The refusal is reported in the batch frame; the socket keeps serving."""
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            batch = await harness.ws_mount_batch(
                communicator,
                [
                    harness.batch_entry(views.LoginRequiredView, "secret", "/secret/"),
                    harness.batch_entry(views.PublicView, "pub", "/public/"),
                ],
            )
            assert batch.get("type") == "mount_batch", batch
            assert "secret" in _targets(batch, "navigate"), batch
            assert "pub" in _targets(batch, "views"), batch
            assert await harness.ws_socket_open(communicator) is True
            await harness.ws_event_runs(communicator, "public_ping", "public_ping")
        finally:
            await harness.ws_close(communicator)


@pytest.mark.django_db
async def test_batch_of_public_views_all_mount():
    with override_settings(**SETTINGS):
        communicator = await harness.ws_connect()
        try:
            batch = await harness.ws_mount_batch(
                communicator,
                [
                    harness.batch_entry(views.PublicView, "one", "/one/"),
                    harness.batch_entry(views.PublicDetailView, "two", "/two/"),
                ],
            )
            assert batch.get("type") == "mount_batch", batch
            assert {"one", "two"} <= set(_targets(batch, "views")), batch
            assert not batch.get("failed"), batch
            await harness.ws_event_runs(communicator, "other_ping", "other_ping")
        finally:
            await harness.ws_close(communicator)
