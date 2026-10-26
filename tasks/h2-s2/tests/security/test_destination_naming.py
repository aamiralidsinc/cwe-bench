"""A request must name its destination host at most once, on receipt and on send."""
from __future__ import annotations

import pytest
from hyperframe.frame import SettingsFrame

import h2.exceptions

from support.frames import (
    FrameBuilder,
    client_connection,
    connected_pair,
    request_headers,
    server_connection,
)


def _matching_last_duplicate():
    # The last regular destination field agrees with the authority; the first does not.
    return request_headers() + [("host", "evil.example"), ("host", "example.com")]


def test_received_request_with_two_destination_fields_is_refused():
    server = server_connection()
    headers = request_headers() + [("host", "evil.example"), ("host", "example.com")]

    with pytest.raises(h2.exceptions.ProtocolError):
        server.receive_data(FrameBuilder().headers(headers).serialize())


def test_received_request_without_authority_but_two_destination_fields_is_refused():
    server = server_connection()
    headers = [
        (":method", "GET"),
        (":scheme", "https"),
        (":path", "/"),
        ("host", "first.example"),
        ("host", "second.example"),
    ]

    with pytest.raises(h2.exceptions.ProtocolError):
        server.receive_data(FrameBuilder().headers(headers).serialize())


def test_sent_request_with_two_destination_fields_is_refused():
    client = client_connection()
    client.clear_outbound_data_buffer()

    with pytest.raises(h2.exceptions.ProtocolError):
        client.send_headers(1, _matching_last_duplicate())

    assert client.data_to_send() == b""


def test_pushed_request_with_two_destination_fields_is_refused():
    client, server = connected_pair()
    client.send_headers(1, request_headers())
    server.receive_data(client.data_to_send())
    server.clear_outbound_data_buffer()

    with pytest.raises(h2.exceptions.ProtocolError):
        server.push_stream(1, 2, _matching_last_duplicate())

    assert server.data_to_send() == b""


def test_received_request_trailer_naming_destination_is_refused():
    server = server_connection()
    builder = FrameBuilder()
    events = server.receive_data(builder.headers(request_headers()).serialize())
    assert [type(event).__name__ for event in events] == ["RequestReceived"]

    trailer = builder.headers([("x-trailer", "1"), ("host", "example.com")], end_stream=True)
    with pytest.raises(h2.exceptions.ProtocolError):
        server.receive_data(trailer.serialize())


def test_sent_request_trailer_naming_destination_is_refused():
    client = client_connection()
    client.send_headers(1, request_headers())
    client.clear_outbound_data_buffer()

    with pytest.raises(h2.exceptions.ProtocolError):
        client.send_headers(1, [("x-trailer", "1"), ("host", "example.com")], end_stream=True)

    assert client.data_to_send() == b""


def test_received_push_promise_with_two_destination_fields_is_refused():
    client = client_connection()
    client.receive_data(SettingsFrame(0).serialize())
    client.send_headers(1, request_headers())
    client.clear_outbound_data_buffer()

    promise = FrameBuilder().push_promise(_matching_last_duplicate())
    with pytest.raises(h2.exceptions.ProtocolError):
        client.receive_data(promise.serialize())
