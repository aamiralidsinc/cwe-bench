"""Legitimate key handling must keep working exactly as today."""
import warnings

from conftest import assert_works

from joserfc import jws, jwt
from joserfc.errors import SecurityWarning
from joserfc.jwk import JWKRegistry, KeySet, OctKey


def test_short_key_warns_and_signs():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        key = OctKey.import_key(b"rfc")
    assert any(issubclass(item.category, SecurityWarning) for item in caught), "short key must keep warning"
    token = assert_works(
        lambda: jws.serialize_compact({"alg": "HS256"}, b"hello", key),
        "short key signs",
    )
    obj = assert_works(lambda: jws.deserialize_compact(token, key), "short key verifies")
    assert obj.payload == b"hello"


def test_short_string_key_works():
    key = OctKey.import_key("secret")
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, key), "short key signs")
    assert assert_works(lambda: jwt.decode(token, key), "short key verifies").claims == {"sub": "ok"}


def test_ordinary_keys_of_every_input_type():
    for value in ("a-real-shared-secret", b"a-real-shared-secret", {"kty": "oct", "k": "c2VjcmV0LXZhbHVl"}):
        key = assert_works(lambda value=value: OctKey.import_key(value), f"import {type(value).__name__}")
        token = assert_works(lambda key=key: jws.serialize_compact({"alg": "HS256"}, b"hello", key), "sign")
        assert assert_works(lambda key=key, token=token: jws.deserialize_compact(token, key), "verify").payload == b"hello"


def test_registry_and_key_set_of_dicts_work():
    jwk_dict = {"kty": "oct", "k": "c2VjcmV0LXZhbHVl"}
    key = assert_works(lambda: JWKRegistry.import_key(dict(jwk_dict)), "registry import")
    assert key.raw_value == b"secret-value"
    keys = assert_works(lambda: KeySet.import_key_set({"keys": [dict(jwk_dict)]}), "key set import")
    token = assert_works(lambda: jwt.encode({"alg": "HS256"}, {"sub": "ok"}, keys), "key set signs")
    assert assert_works(lambda: jwt.decode(token, keys), "key set verifies").claims == {"sub": "ok"}


def test_all_hmac_algorithms_work():
    key = OctKey.import_key("a-real-shared-secret")
    for alg in ("HS256", "HS384", "HS512"):
        token = assert_works(
            lambda alg=alg: jws.serialize_compact({"alg": alg}, b"hello", key, algorithms=[alg]),
            f"{alg} sign",
        )
        obj = assert_works(
            lambda alg=alg, token=token: jws.deserialize_compact(token, key, algorithms=[alg]),
            f"{alg} verify",
        )
        assert obj.payload == b"hello"


def test_json_serializations_work():
    key = OctKey.import_key("a-real-shared-secret")
    flat = assert_works(lambda: jws.serialize_json({"protected": {"alg": "HS256"}}, b"hello", key), "flattened")
    assert assert_works(lambda: jws.deserialize_json(flat, key), "flattened verify").payload == b"hello"
    general = assert_works(
        lambda: jws.serialize_json([{"protected": {"alg": "HS256"}}], b"hello", key), "general"
    )
    assert assert_works(lambda: jws.deserialize_json(general, key), "general verify").payload == b"hello"


def test_unencoded_payload_works():
    key = OctKey.import_key("a-real-shared-secret")
    header = {"alg": "HS256", "b64": False, "crit": ["b64"]}
    token = assert_works(lambda: jws.serialize_compact(header, b"hello", key), "RFC 7797 sign")
    obj = assert_works(lambda: jws.deserialize_compact(token, key), "RFC 7797 verify")
    assert obj.payload == b"hello"
