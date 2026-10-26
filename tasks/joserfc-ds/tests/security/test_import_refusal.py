"""Every public way of loading an empty secret must refuse it.

The reported symptom is an accepted token, but the invariant is over the secret itself:
a secret that carries no key material must not be turned into a key, whichever loader
is used and whichever input shape it takes.
"""
from conftest import assert_refused

from joserfc import jwk
from joserfc.jwk import JWKRegistry, KeySet, OctKey

EMPTY_JWK = {"kty": "oct", "k": ""}


def test_oct_key_refuses_empty_string():
    assert_refused(lambda: OctKey.import_key(""), "oct key from empty string")


def test_oct_key_refuses_empty_bytes():
    assert_refused(lambda: OctKey.import_key(b""), "oct key from empty bytes")


def test_oct_key_refuses_empty_jwk_member():
    assert_refused(lambda: OctKey.import_key(dict(EMPTY_JWK)), "oct key from empty JWK")


def test_jwk_import_refuses_empty_string_with_type():
    assert_refused(lambda: jwk.import_key("", "oct"), "import_key with explicit oct type")


def test_jwk_import_refuses_empty_jwk():
    assert_refused(lambda: jwk.import_key(dict(EMPTY_JWK)), "import_key with empty JWK")


def test_registry_refuses_empty_jwk():
    assert_refused(lambda: JWKRegistry.import_key(dict(EMPTY_JWK)), "registry bulk import")


def test_key_set_refuses_empty_jwk():
    assert_refused(
        lambda: KeySet.import_key_set({"keys": [dict(EMPTY_JWK)]}),
        "key set with an empty oct member",
    )


def test_empty_jwk_does_not_yield_a_key_object():
    def load():
        key = OctKey.import_key(dict(EMPTY_JWK))
        return key.raw_value

    assert_refused(load, "empty JWK yielded key material")
