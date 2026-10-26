"""An empty plain secret must not be turned into usable key material.

When the configured secret is a plain value, the library prepares the MAC key from it
before the signature check. An empty value therefore reaches the check as a non-empty
derived key unless the supplied value itself is refused.
"""
import hashlib

from conftest import assert_refused, compact_token, flattened_token

from joserfc import jws, jwt

# The fixed value the implementation prepares from an empty plain secret; an attacker
# can reproduce it trivially, so a token built with it must never verify.
DERIVED_EMPTY = hashlib.sha256(b"").digest()


def test_jwt_decode_refuses_empty_string_secret():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, DERIVED_EMPTY)
    assert_refused(lambda: jwt.decode(token, ""), "JWT verified with an empty plain secret")


def test_jwt_decode_refuses_empty_bytes_secret():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, DERIVED_EMPTY)
    assert_refused(lambda: jwt.decode(token, b""), "JWT verified with empty bytes")


def test_jwt_decode_refuses_empty_bytearray_secret():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, DERIVED_EMPTY)
    assert_refused(lambda: jwt.decode(token, bytearray()), "JWT verified with empty bytearray")


def test_jwt_encode_refuses_empty_string_secret():
    assert_refused(
        lambda: jwt.encode({"alg": "HS256"}, {"sub": "admin"}, ""),
        "JWT signed with an empty plain secret",
    )


def test_jwt_encode_refuses_empty_bytes_secret():
    assert_refused(
        lambda: jwt.encode({"alg": "HS256"}, {"sub": "admin"}, b""),
        "JWT signed with empty bytes",
    )


def test_compact_verify_refuses_empty_secret():
    token = compact_token({"alg": "HS256"}, b"hello", DERIVED_EMPTY)
    assert_refused(lambda: jws.deserialize_compact(token, ""), "compact JWS verified")


def test_compact_sign_refuses_empty_secret():
    assert_refused(
        lambda: jws.serialize_compact({"alg": "HS256"}, b"hello", ""),
        "compact JWS signed",
    )


def test_flattened_json_verify_refuses_empty_secret():
    value = flattened_token({"alg": "HS256"}, b"hello", DERIVED_EMPTY)
    assert_refused(lambda: jws.deserialize_json(value, ""), "flattened JSON JWS verified")


def test_key_finder_returning_empty_secret_refused():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, DERIVED_EMPTY)
    assert_refused(lambda: jwt.decode(token, lambda obj: ""), "key finder returned an empty secret")


def test_key_finder_returning_empty_bytes_refused():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, DERIVED_EMPTY)
    assert_refused(lambda: jwt.decode(token, lambda obj: b""), "key finder returned empty bytes")
