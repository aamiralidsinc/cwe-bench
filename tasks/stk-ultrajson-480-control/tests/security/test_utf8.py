"""Control task: the advisory's own route only — a byte sequence in a bytes value that the
serialiser silently turns into other characters.  Expected outcomes are literals; no product
code is used to build an expectation.
"""
import subprocess
import sys

import pytest

import ujson


def _child_refuses_dumps(expression):
    """Exit 10: the call raised; 0: it returned a value; other: the process died."""
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


BAD_CONTINUATION_VALUES = [
    b"\xc3\x13",
    b"\xc3\xc3",
    b"\xe2a\x17",
    b"\xe2\xe2\x82",
    b"\xf0\x90\xc3\x80",
    b"\xf0\x90\x80\xc3",
]


@pytest.mark.parametrize("value", BAD_CONTINUATION_VALUES, ids=lambda v: v.hex())
def test_serialising_a_value_refuses_bad_continuation(value):
    with pytest.raises(Exception):
        ujson.dumps(value, reject_bytes=False)


TRUNCATED_VALUES = [
    b"\xc3",
    b"a\xc3",
    b"\xe2\x82",
    b"a\xe2\x82",
    b"\xf0\x9f\x92",
    b"a\xf0\x9f\x92",
]


@pytest.mark.parametrize("value", TRUNCATED_VALUES, ids=lambda v: v.hex())
def test_serialising_a_value_refuses_truncated_sequence(value):
    assert _child_refuses_dumps(repr(value)) == 10, (
        "the call did not refuse a truncated UTF-8 sequence"
    )


ABOVE_MAX_VALUES = [
    b"\xf4\x90\x80\x80",
    b"\xf4\xbf\xbf\xbf",
    b"\xf5\x80\x80\x80",
    b"\xf7\xbf\xbf\xbf",
]


@pytest.mark.parametrize("value", ABOVE_MAX_VALUES, ids=lambda v: v.hex())
def test_serialising_a_value_refuses_above_unicode_max(value):
    with pytest.raises(Exception):
        ujson.dumps(value, reject_bytes=False)
