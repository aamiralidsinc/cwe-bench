"""The frame-size handling that already works keeps working.

A deployment may configure a large response limit (the consumer asks brokers for responses of
tens of megabytes), and the library's documented default is larger still.  A frame that fits
inside the limit stays acceptable; one that does not is still refused.
"""

import struct

import pytest

from kafka.errors import InvalidReceiveError
from kafka.protocol.parser import KafkaProtocol

LARGE_FRAME = 52428800  # the client's default fetch size


def test_large_configured_frame_is_accepted():
    parser = KafkaProtocol(client_id='functional', receive_message_max_bytes=LARGE_FRAME)
    parser.receive_bytes(struct.pack('>i', LARGE_FRAME))


def test_large_frame_with_the_documented_default_is_accepted():
    parser = KafkaProtocol(client_id='functional')
    parser.receive_bytes(struct.pack('>i', LARGE_FRAME))


def test_frame_above_the_default_limit_is_still_refused():
    parser = KafkaProtocol(client_id='functional')
    with pytest.raises(InvalidReceiveError):
        parser.receive_bytes(struct.pack('>i', 100000001))
