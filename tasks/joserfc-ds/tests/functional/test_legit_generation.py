"""Key generation keeps working for ordinary and short sizes."""
import warnings

from conftest import assert_works

from joserfc import jwk
from joserfc.errors import SecurityWarning
from joserfc.jwk import OctKey


def test_default_generation():
    key = assert_works(lambda: jwk.generate_key("oct"), "default key")
    assert len(key.raw_value) == 32


def test_ordinary_sizes():
    for bits in (112, 128, 192, 256, 512):
        key = assert_works(lambda bits=bits: jwk.generate_key("oct", bits), f"{bits}-bit key")
        assert len(key.raw_value) == bits // 8


def test_short_generation_still_warns_and_works():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        key = assert_works(lambda: OctKey.generate_key(16), "16-bit key")
    assert len(key.raw_value) == 2
    assert any(issubclass(item.category, SecurityWarning) for item in caught), "short generation must keep warning"


def test_generated_keys_sign_and_verify():
    key = assert_works(lambda: jwk.generate_key("oct", 256), "256-bit key")
    from joserfc import jws

    token = assert_works(lambda: jws.serialize_compact({"alg": "HS256"}, b"hello", key), "sign")
    assert assert_works(lambda: jws.deserialize_compact(token, key), "verify").payload == b"hello"
