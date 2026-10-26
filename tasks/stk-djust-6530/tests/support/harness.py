"""Driving helpers for the hidden suites.

The helpers only use the product's public entry points: the WebSocket consumer's
frame protocol and the SSE stream/event views. They compute every expected value
and clean-up themselves, so a hardened product helper cannot break a test.
"""

from __future__ import annotations

import asyncio
import json
import uuid

from support import views


def view_path(view_class) -> str:
    return f"{view_class.__module__}.{view_class.__name__}"


async def _next_output(communicator, timeout):
    """Read one queued output frame without cancelling the consumer on timeout.

    channels' ``receive_output`` cancels the application when nothing arrives,
    which would turn "the refusal sent no frame" into a dead session.
    """
    try:
        async with asyncio.timeout(timeout):
            return await communicator.output_queue.get()
    except (TimeoutError, asyncio.TimeoutError):
        return None


# --------------------------------------------------------------------------- #
# WebSocket transport
# --------------------------------------------------------------------------- #


async def ws_connect(user=None):
    """Open a WebSocket session and drain the connect frame."""
    from channels.testing import WebsocketCommunicator

    from djust.websocket import LiveViewConsumer

    communicator = WebsocketCommunicator(LiveViewConsumer.as_asgi(), "/ws/")
    if user is not None:
        communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected, "WebSocket handshake was rejected"
    hello = await communicator.receive_json_from(timeout=10)
    assert hello.get("type") == "connect", f"expected connect frame, got {hello!r}"
    return communicator


async def ws_mount(communicator, view_class, target_id="", url="/", timeout=10):
    await communicator.send_json_to(
        {
            "type": "mount",
            "view": view_path(view_class),
            "url": url,
            "target_id": target_id,
        }
    )
    return await communicator.receive_json_from(timeout=timeout)


async def ws_live_redirect_mount(communicator, view_class, url="/", timeout=10):
    await communicator.send_json_to(
        {
            "type": "live_redirect_mount",
            "view": view_path(view_class),
            "url": url,
        }
    )
    return await communicator.receive_json_from(timeout=timeout)


async def ws_mount_batch(communicator, entries, timeout=10):
    await communicator.send_json_to({"type": "mount_batch", "views": entries})
    return await communicator.receive_json_from(timeout=timeout)


def batch_entry(view_class, target_id, url="/"):
    return {
        "view": view_path(view_class),
        "target_id": target_id,
        "url": url,
        "params": {},
    }


async def ws_event_refused(communicator, event, marker, timeout=10):
    """Send one event and require that the handler did not run.

    A refusal may terminate the transport, send an error frame, or leave the
    socket open with no dispatch at all; a successful dispatch answers with a
    noop/patch frame instead. Any of the first three is accepted.
    """
    before = len(views.EXECUTED)
    try:
        await communicator.send_json_to({"type": "event", "event": event, "params": {}})
    except Exception:  # noqa: BLE001 - a closed transport is a valid refusal
        pass
    out = await _next_output(communicator, timeout)
    assert marker not in views.EXECUTED[before:], (
        f"refused mount still dispatched {event!r}: {views.EXECUTED[before:]!r}"
    )
    if out is None:
        return
    if out.get("type") == "websocket.close":
        return
    assert out.get("type") == "websocket.send", f"unexpected frame after refusal: {out!r}"
    payload = json.loads(out.get("text") or "{}")
    assert payload.get("type") == "error", f"refused event produced a success frame: {payload!r}"


async def ws_event_runs(communicator, event, marker, timeout=10):
    """Send one event and require that its handler ran."""
    before = len(views.EXECUTED)
    await communicator.send_json_to({"type": "event", "event": event, "params": {}})
    out = await _next_output(communicator, timeout)
    assert marker in views.EXECUTED[before:], (
        f"legitimate mount did not dispatch {event!r}: {views.EXECUTED[before:]!r}"
    )
    assert out is not None and out.get("type") == "websocket.send", f"unexpected frame: {out!r}"


async def ws_socket_open(communicator, timeout=1.0):
    """True when the shared socket is still usable (no close frame waiting)."""
    return await communicator.receive_nothing(timeout=timeout)


async def ws_close(communicator):
    """Best-effort teardown; a refused/closed socket is a normal ending."""
    try:
        await communicator.disconnect()
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- #
# SSE transport
# --------------------------------------------------------------------------- #


async def sse_mount(view_class, user=None):
    """Open an SSE stream for one view through the product's stream view."""
    from django.test import RequestFactory

    from djust.sse import DjustSSEStreamView, _sse_sessions

    session_id = str(uuid.uuid4())
    request = RequestFactory().get(
        f"/djust/sse/{session_id}/?view={view_path(view_class)}"
    )
    if user is not None:
        request.user = user
    response = await DjustSSEStreamView.as_view()(request, session_id=session_id)
    session = _sse_sessions.get(session_id)
    assert session is not None, "SSE stream view did not register a session"
    return session_id, session, response


def sse_messages(session):
    """Drain the messages the stream would have delivered so far."""
    out = []
    while not session.queue.empty():
        out.append(session.queue.get_nowait())
    return out


async def sse_event(session_id, event):
    """POST one event through the product's event view."""
    from django.test import RequestFactory

    from djust.sse import DjustSSEEventView

    request = RequestFactory().post(
        f"/djust/sse/{session_id}/event/",
        data=json.dumps({"event": event, "params": {}}),
        content_type="application/json",
    )
    return await DjustSSEEventView.as_view()(request, session_id=session_id)


def sse_forget(session_id):
    from djust.sse import _sse_sessions

    _sse_sessions.pop(session_id, None)
