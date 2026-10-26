"""A key set built from a rotation list must refuse empty plain secrets.

The collection surface builds key objects from the list's entries itself; an empty entry
must not become a usable key.
"""
from conftest import assert_refused, compact_token

from joserfc import jwt
from joserfc.jwk import KeySet


def test_key_set_refuses_empty_string_secret():
    assert_refused(
        lambda: KeySet.import_key_set({"keys": [""]}),
        "key set built from an empty plain secret",
    )


def test_key_set_refuses_empty_bytes_secret():
    assert_refused(
        lambda: KeySet.import_key_set({"keys": [b""]}),
        "key set built from empty bytes",
    )


def test_key_set_empty_secret_cannot_authenticate():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, b"")

    def use():
        keys = KeySet.import_key_set({"keys": [""]})
        return jwt.decode(token, keys)

    assert_refused(use, "key set with an empty secret authenticated a token")


def test_mixed_key_set_refuses_empty_entry():
    assert_refused(
        lambda: KeySet.import_key_set(
            {"keys": ["a-real-secret-value", {"kty": "oct", "k": "c2VjcmV0LXZhbHVl"}, ""]}
        ),
        "one empty entry among real secrets",
    )
