"""Legitimate requests keep working exactly as before."""
from __future__ import annotations

import h2.config

from support.frames import (
    FrameBuilder,
    client_connection,
    connected_pair,
    request_headers,
    server_connection,
)


def _events_of(events, name):
    return [event for event in events if type(event).__name__ == name]


def test_matching_authority_and_host_is_accepted():
    server = server_connection()
    headers = request_headers() + [("host", "example.com")]

    events = server.receive_data(FrameBuilder().headers(headers).serialize())

    received = _events_of(events, "RequestReceived")
    assert len(received) == 1
    assert (b":authority", b"example.com") in received[0].headers
    assert (b"host", b"example.com") in received[0].headers


def test_authority_only_and_host_only_are_accepted():
    authority_only = server_connection()
    events = authority_only.receive_data(
        FrameBuilder().headers(request_headers()).serialize(),
    )
    assert len(_events_of(events, "RequestReceived")) == 1

    host_only = server_connection()
    headers = [
        (":method", "GET"),
        (":scheme", "https"),
        (":path", "/"),
        ("host", "example.com"),
    ]
    events = host_only.receive_data(FrameBuilder().headers(headers).serialize())
    assert len(_events_of(events, "RequestReceived")) == 1


def test_sent_request_with_matching_pair_round_trips():
    client, server = connected_pair()
    headers = request_headers() + [("host", "example.com")]

    client.send_headers(1, headers, end_stream=True)
    events = server.receive_data(client.data_to_send())

    received = _events_of(events, "RequestReceived")
    assert len(received) == 1
    assert (b"host", b"example.com") in received[0].headers


def test_split_outbound_cookies_round_trip():
    client_config = h2.config.H2Configuration(
        client_side=True, header_encoding="utf-8", split_outbound_cookies=True,
    )
    server_config = h2.config.H2Configuration(
        client_side=False, header_encoding="utf-8", normalize_inbound_headers=False,
    )
    client, server = connected_pair(client_config, server_config)
    headers = request_headers() + [
        ("cookie", "first=1; second=2"),
        ("cookie", "third=3"),
    ]

    client.send_headers(1, headers, end_stream=True)
    events = server.receive_data(client.data_to_send())

    received = _events_of(events, "RequestReceived")
    assert len(received) == 1
    cookies = [field for field in received[0].headers if field[0] == "cookie"]
    assert cookies == [
        ("cookie", "first=1"),
        ("cookie", "second=2"),
        ("cookie", "third=3"),
    ]


def test_repeated_identical_content_length_is_accepted():
    server = server_connection()
    headers = request_headers() + [("content-length", "0"), ("content-length", "0")]

    events = server.receive_data(
        FrameBuilder().headers(headers, end_stream=True).serialize(),
    )

    received = _events_of(events, "RequestReceived")
    assert len(received) == 1
    lengths = [field for field in received[0].headers if field[0] == b"content-length"]
    assert lengths == [
        (b"content-length", b"0"),
        (b"content-length", b"0"),
    ]


def test_received_request_trailer_without_destination_is_accepted():
    server = server_connection()
    builder = FrameBuilder()
    server.receive_data(builder.headers(request_headers()).serialize())
    trailer = builder.headers([("x-trailer", "1")], end_stream=True)

    events = server.receive_data(trailer.serialize())

    trailers = _events_of(events, "TrailersReceived")
    assert len(trailers) == 1
    assert (b"x-trailer", b"1") in trailers[0].headers


def test_sent_request_trailer_without_destination_is_accepted():
    client, server = connected_pair()
    client.send_headers(1, request_headers())
    server.receive_data(client.data_to_send())
    client.clear_outbound_data_buffer()

    client.send_headers(1, [("x-trailer", "1")], end_stream=True)
    events = server.receive_data(client.data_to_send())

    trailers = _events_of(events, "TrailersReceived")
    assert len(trailers) == 1
    assert (b"x-trailer", b"1") in trailers[0].headers


def test_pushed_request_with_single_destination_is_accepted():
    client, server = connected_pair()
    client.send_headers(1, request_headers())
    server.receive_data(client.data_to_send())
    client.clear_outbound_data_buffer()
    server.clear_outbound_data_buffer()

    server.push_stream(
        1,
        2,
        [
            (":method", "GET"),
            (":scheme", "https"),
            (":path", "/pushed"),
            (":authority", "example.com"),
            ("host", "example.com"),
        ],
    )
    events = client.receive_data(server.data_to_send())

    pushed = _events_of(events, "PushedStreamReceived")
    assert len(pushed) == 1
    assert (b"host", b"example.com") in pushed[0].headers
