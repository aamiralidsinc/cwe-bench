"""Key material that is empty must not be produced in the first place.

A zero-length key is a key whose MAC is reproducible by anyone. It must not be handed
back as a usable key, and if it somehow exists it must not authenticate.
"""
from conftest import assert_refused, compact_token

from joserfc import jwk, jws
from joserfc.jwk import OctKey


def test_generate_zero_bits_refused():
    assert_refused(lambda: jwk.generate_key("oct", 0), "zero-bit oct key generated")


def test_oct_key_generate_zero_bits_refused():
    assert_refused(lambda: OctKey.generate_key(0), "zero-bit oct key generated directly")


def test_zero_length_material_cannot_authenticate():
    token = compact_token({"alg": "HS256"}, b"hello", b"")

    def use():
        key = jwk.generate_key("oct", 0)
        return jws.deserialize_compact(token, key)

    assert_refused(use, "zero-length key verified a MAC")
