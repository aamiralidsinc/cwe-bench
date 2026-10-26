"""Frame and connection helpers for the hidden suites.

These are computed here rather than imported from the project's own test helpers: the suites
must keep working even when the submitted tree has changed its test support code.
"""
from __future__ import annotations

from hpack import Encoder
from hyperframe.frame import HeadersFrame, PushPromiseFrame

import h2.config
import h2.connection

PREAMBLE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"


class FrameBuilder:
    def __init__(self) -> None:
        self.encoder = Encoder()

    def headers(self, headers, stream_id=1, end_stream=False):
        frame = HeadersFrame(stream_id)
        frame.data = self.encoder.encode(headers)
        frame.flags.add("END_HEADERS")
        if end_stream:
            frame.flags.add("END_STREAM")
        return frame

    def push_promise(self, headers, stream_id=1, promised_stream_id=2):
        frame = PushPromiseFrame(stream_id)
        frame.promised_stream_id = promised_stream_id
        frame.data = self.encoder.encode(headers)
        frame.flags.add("END_HEADERS")
        return frame


def server_connection(received_preamble=True):
    """A server-side connection positioned just after the client preface."""
    conn = h2.connection.H2Connection(config=h2.config.H2Configuration(client_side=False))
    conn.initiate_connection()
    if received_preamble:
        conn.receive_data(PREAMBLE)
    conn.clear_outbound_data_buffer()
    return conn


def client_connection(config=None):
    conn = h2.connection.H2Connection(
        config=config or h2.config.H2Configuration(client_side=True),
    )
    conn.initiate_connection()
    return conn


def connected_pair(client_config=None, server_config=None):
    """A client and a server whose prefaces and settings have been exchanged."""
    client = client_connection(client_config)
    server = h2.connection.H2Connection(
        config=server_config or h2.config.H2Configuration(client_side=False),
    )
    server.initiate_connection()
    server.receive_data(client.data_to_send())
    client.receive_data(server.data_to_send())
    return client, server


def request_headers(authority="example.com"):
    return [
        (":method", "GET"),
        (":scheme", "https"),
        (":path", "/"),
        (":authority", authority),
    ]
