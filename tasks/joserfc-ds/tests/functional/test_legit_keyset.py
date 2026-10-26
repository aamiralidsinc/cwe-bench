"""A key set built from a rotation list keeps working for real secrets."""
from conftest import assert_works

from joserfc import jwt
from joserfc.jwk import KeySet


def test_plain_secret_in_key_set_roundtrip():
    keys = assert_works(lambda: KeySet.import_key_set({"keys": ["rotation-secret-value"]}), "key set import")
    assert [key.raw_value for key in keys.keys] == [b"rotation-secret-value"]
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, keys), "sign")
    assert assert_works(lambda: jwt.decode(token, keys), "verify").claims == {"sub": "ok"}


def test_mixed_key_set_roundtrip():
    keys = assert_works(
        lambda: KeySet.import_key_set(
            {"keys": ["rotation-secret-value", {"kty": "oct", "k": "b3RoZXItc2VjcmV0LXZhbHVl"}]}
        ),
        "mixed key set import",
    )
    assert len(keys.keys) == 2
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, keys), "sign")
    assert assert_works(lambda: jwt.decode(token, keys), "verify").claims == {"sub": "ok"}
