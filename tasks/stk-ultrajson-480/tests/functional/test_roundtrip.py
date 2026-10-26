"""Legitimate use keeps working exactly as today.

Expected values are literals or are computed with the standard library; no product code is used
to build an expectation, so a hardened helper cannot make a test agree with itself.
"""
import array
import json

import pytest

import ujson


VALID_UTF8 = [
    b"",
    b"plain ascii",
    b"\x00",
    b"\x7f",
    b"h\xc3\xa9llo",
    b"\xc2\x80",
    b"\xdf\xbf",
    b"\xe2\x82\xac",
    b"\xef\xbf\xbf",
    b"\xf0\x9f\xa6\x84",
    b"a\xf0\x9f\x92\xa9b",
    b"caf\xc3\xa9 \xe2\x82\xac \xf0\x9f\xa6\x84",
]


def _id(raw):
    return raw.hex() or "empty"


@pytest.mark.parametrize("raw", VALID_UTF8, ids=_id)
def test_bytes_value_keeps_its_characters(raw):
    dumped = ujson.dumps(raw, reject_bytes=False)
    assert json.loads(dumped) == raw.decode("utf-8")


@pytest.mark.parametrize("raw", VALID_UTF8, ids=_id)
def test_bytes_key_keeps_its_characters(raw):
    dumped = ujson.dumps({raw: "value"}, reject_bytes=False)
    assert json.loads(dumped) == {raw.decode("utf-8"): "value"}


def test_nested_bytes_keep_their_characters():
    data = {"a": [b"caf\xc3\xa9", {b"k\xe2\x82\xac": b"\xf0\x9f\xa6\x84"}]}
    dumped = ujson.dumps(data, reject_bytes=False)
    assert json.loads(dumped) == {"a": ["café", {"k€": "🦄"}]}


# --- the project's existing representation of surrogate code points ---------------------
def test_bytes_surrogate_value_is_represented_as_today():
    assert ujson.dumps(b"\xed\xa0\x80", reject_bytes=False) == '"\\ud800"'
    assert ujson.dumps(b"\xed\xbf\xbf", reject_bytes=False) == '"\\udfff"'


def test_bytes_surrogate_key_is_represented_as_today():
    expected = '{"\\ud800":"\\udfff"}'
    data = {b"\xed\xa0\x80": b"\xed\xbf\xbf"}
    assert ujson.dumps(data, reject_bytes=False) == expected
    assert ujson.dumps(data, reject_bytes=False, sort_keys=True) == expected


def test_str_surrogates_are_represented_as_today():
    assert ujson.dumps("\ud800") == '"\\ud800"'
    assert ujson.dumps({"\ud800": "\udfff"}) == '{"\\ud800":"\\udfff"}'
    assert ujson.dumps("\ud800", ensure_ascii=False) == '"\ud800"'
    assert ujson.dumps({"\ud800": "\udfff"}, ensure_ascii=False) == '{"\ud800":"\udfff"}'


def test_parsing_keeps_surrogate_values():
    assert ujson.loads(b'"\xed\xa0\x80"') == "\ud800"
    assert ujson.loads(b'"\xed\xbf\xbf"') == "\udfff"
    assert ujson.loads('"\\uD800"') == "\ud800"
    assert ujson.loads(ujson.dumps(b"\xed\xa0\x80", reject_bytes=False)) == "\ud800"


# --- ordinary text and the input types the library accepts ------------------------------
def test_unicode_text_roundtrips():
    for text in ["héllo", "€", "🦄", "a\u0000b", "plain"]:
        assert ujson.loads(ujson.dumps(text)) == text
        assert ujson.loads(ujson.dumps(text, ensure_ascii=False)) == text


def test_loads_still_accepts_buffer_protocol_inputs():
    assert ujson.loads(memoryview(b'["a", "b", "c"]')) == ["a", "b", "c"]
    assert ujson.loads(bytearray(b"99")) == 99
    assert ujson.loads(array.array("B", b'{"a":1}')) == {"a": 1}


def test_reject_bytes_policy_is_unchanged():
    with pytest.raises(TypeError):
        ujson.dumps(b"hello")
    with pytest.raises(TypeError):
        ujson.dumps({"a": [b"deep"]})
    assert ujson.dumps(b"hello", reject_bytes=False) == '"hello"'
    assert ujson.dumps({"a": b"b"}, reject_bytes=False) == '{"a":"b"}'
