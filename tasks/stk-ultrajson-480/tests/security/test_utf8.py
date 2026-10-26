"""The library must refuse a byte sequence that does not encode exactly one code point,
instead of representing it as some other code point, in both conversion directions.

Every case drives only the public library API.  Expected outcomes are literals or are
computed with the standard library; no product code is used to build an expectation.
"""
import subprocess
import sys

import pytest

import ujson


def _child_refuses_dumps(expression):
    """Serialise one expression in a child process and report how it ended.

    Exit 10: the call raised an error (a refusal).
    Exit 0:  the call returned a value (the bad bytes were silently rewritten).
    Other:   the process died or the module failed to load (not a clean refusal).
    A child process is used for the end-of-buffer cases because the vulnerable code can read
    past its input there; isolating it keeps one bad case from taking the whole run down.
    """
    source = (
        "import sys, ujson\n"
        "try:\n"
        "    ujson.dumps(%s, reject_bytes=False)\n"
        "except Exception:\n"
        "    sys.exit(10)\n"
        "sys.exit(0)\n" % expression
    )
    proc = subprocess.run(
        [sys.executable, "-c", source], capture_output=True, text=True, timeout=120
    )
    return proc.returncode


# --- encoder: a byte in a continuation position that is not 0b10xxxxxx ------------------
BAD_CONTINUATION_VALUES = [
    b"\xc3\x13",          # 2-byte arm, second byte is not a continuation byte
    b"\xc3\xc3",          # 2-byte arm, second byte is itself a start byte
    b"\xe2a\x17",         # 3-byte arm
    b"\xe2\xe2\x82",      # 3-byte arm, second byte is itself a start byte
    b"\xf0\x90\xc3\x80",  # 4-byte arm, third byte is itself a start byte
    b"\xf0\x90\x80\xc3",  # 4-byte arm, fourth byte is itself a start byte
]


@pytest.mark.parametrize("value", BAD_CONTINUATION_VALUES, ids=lambda v: v.hex())
def test_serialising_a_value_refuses_bad_continuation(value):
    with pytest.raises(Exception):
        ujson.dumps(value, reject_bytes=False)


@pytest.mark.parametrize("value", BAD_CONTINUATION_VALUES, ids=lambda v: v.hex())
def test_serialising_a_key_refuses_bad_continuation(value):
    with pytest.raises(Exception):
        ujson.dumps({value: 1}, reject_bytes=False)


# --- encoder: a sequence cut short at the end of the buffer -----------------------------
TRUNCATED_VALUES = [
    b"\xc3",              # 2-byte arm, one byte short
    b"a\xc3",
    b"\xe2\x82",          # 3-byte arm, one byte short
    b"a\xe2\x82",
    b"\xf0\x9f\x92",      # 4-byte arm, one byte short
    b"a\xf0\x9f\x92",
]


@pytest.mark.parametrize("value", TRUNCATED_VALUES, ids=lambda v: v.hex())
def test_serialising_a_value_refuses_truncated_sequence(value):
    assert _child_refuses_dumps(repr(value)) == 10, (
        "the call did not refuse a truncated UTF-8 sequence"
    )


@pytest.mark.parametrize("value", [b"\xc3", b"\xe2\x82", b"\xf0\x9f\x92"], ids=lambda v: v.hex())
def test_serialising_a_key_refuses_truncated_sequence(value):
    assert _child_refuses_dumps("{%r: 1}" % value) == 10, (
        "the call did not refuse a truncated UTF-8 sequence in a key"
    )


# --- encoder: a 4-byte sequence above U+10FFFF ------------------------------------------
ABOVE_MAX_VALUES = [
    b"\xf4\x90\x80\x80",  # U+110000
    b"\xf4\xbf\xbf\xbf",
    b"\xf5\x80\x80\x80",
    b"\xf7\xbf\xbf\xbf",
]


@pytest.mark.parametrize("value", ABOVE_MAX_VALUES, ids=lambda v: v.hex())
def test_serialising_a_value_refuses_above_unicode_max(value):
    with pytest.raises(Exception):
        ujson.dumps(value, reject_bytes=False)


@pytest.mark.parametrize("value", ABOVE_MAX_VALUES, ids=lambda v: v.hex())
def test_serialising_a_key_refuses_above_unicode_max(value):
    with pytest.raises(Exception):
        ujson.dumps({value: 1}, reject_bytes=False)


# --- decoder: a byte in a continuation position that is not 0b10xxxxxx ------------------
BAD_CONTINUATION_DOCUMENTS = [
    b'"\xc3\xc3"',        # 2-byte arm
    b'"\xe2\xe2\x82"',    # 3-byte arm
    b'"\xf0\xf0\x80\x80"',# 4-byte arm, second byte is a start byte
    b'"\xf0\x90\xc3\x80"',# 4-byte arm, third byte is a start byte
]


@pytest.mark.parametrize(
    "document",
    BAD_CONTINUATION_DOCUMENTS,
    ids=["2-byte-arm", "3-byte-arm", "4-byte-arm-second", "4-byte-arm-third"],
)
def test_parsing_refuses_bad_continuation(document):
    with pytest.raises(Exception):
        ujson.loads(document)


# --- decoder: a continuation byte where a start byte is required ------------------------
LONE_CONTINUATION_DOCUMENTS = [
    b'"\x9b"',
    b'"\x80"',
    b'"\xbf"',
    b'"a\x9bb"',
]


@pytest.mark.parametrize(
    "document", LONE_CONTINUATION_DOCUMENTS, ids=["9b", "80", "bf", "embedded"]
)
def test_parsing_refuses_continuation_lead_byte(document):
    with pytest.raises(Exception):
        ujson.loads(document)
