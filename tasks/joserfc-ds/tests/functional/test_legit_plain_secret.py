"""A non-empty plain secret keeps working exactly as today.

The convenience that accepts a plain configured secret must not be removed by the fix.
"""
from conftest import assert_works

from joserfc import jws, jwt


def test_plain_string_secret_roundtrip():
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, "my-secret"), "encode")
    assert assert_works(lambda: jwt.decode(token, "my-secret"), "decode").claims == {"sub": "ok"}


def test_plain_bytes_secret_roundtrip():
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, b"my-secret"), "encode")
    assert assert_works(lambda: jwt.decode(token, b"my-secret"), "decode").claims == {"sub": "ok"}


def test_plain_secret_compact_jws():
    token = assert_works(lambda: jws.serialize_compact({"alg": "HS256"}, b"hello", "my-secret"), "sign")
    assert assert_works(lambda: jws.deserialize_compact(token, "my-secret"), "verify").payload == b"hello"


def test_plain_secret_json_jws():
    value = assert_works(
        lambda: jws.serialize_json({"protected": {"alg": "HS256"}}, b"hello", "my-secret"), "sign"
    )
    assert assert_works(lambda: jws.deserialize_json(value, "my-secret"), "verify").payload == b"hello"


def test_plain_secret_through_key_finder():
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, "my-secret"), "encode")
    result = assert_works(lambda: jwt.decode(token, lambda obj: "my-secret"), "key finder")
    assert result.claims == {"sub": "ok"}


def test_long_plain_secret_roundtrip():
    secret = "a-much-longer-shared-secret-for-rotation"
    token = assert_works(lambda: jwt.encode({"alg": "HS512"}, {"sub": "ok"}, secret, algorithms=["HS512"]), "encode")
    result = assert_works(lambda: jwt.decode(token, secret, algorithms=["HS512"]), "decode")
    assert result.claims == {"sub": "ok"}
