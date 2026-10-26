"""Authentication must never succeed with empty key material.

Attack tokens are built from scratch with the standard library, so this suite does not
depend on the product being able to sign with an empty key. The key object handed to the
verifier is built directly, bypassing every key loader.
"""
import hashlib

from conftest import assert_refused, b64_token, compact_token, flattened_token, general_token

from joserfc import jws, jwt
from joserfc.jwk import OctKey

EMPTY = b""


def _empty_key():
    return OctKey(EMPTY, EMPTY)


def test_jwt_decode_refuses_empty_key():
    token = compact_token({"alg": "HS256"}, {"sub": "admin"}, EMPTY)
    assert_refused(lambda: jwt.decode(token, _empty_key()), "JWT verified with an empty key")


def test_jwt_encode_refuses_empty_key():
    assert_refused(
        lambda: jwt.encode({"alg": "HS256"}, {"sub": "admin"}, _empty_key()),
        "JWT signed with an empty key",
    )


def test_compact_verify_refuses_empty_key():
    token = compact_token({"alg": "HS256"}, b"hello", EMPTY)
    assert_refused(lambda: jws.deserialize_compact(token, _empty_key()), "compact JWS verified")


def test_compact_sign_refuses_empty_key():
    assert_refused(
        lambda: jws.serialize_compact({"alg": "HS256"}, b"hello", _empty_key()),
        "compact JWS signed",
    )


def test_flattened_json_verify_refuses_empty_key():
    value = flattened_token({"alg": "HS256"}, b"hello", EMPTY)
    assert_refused(lambda: jws.deserialize_json(value, _empty_key()), "flattened JSON JWS verified")


def test_flattened_json_sign_refuses_empty_key():
    assert_refused(
        lambda: jws.serialize_json({"protected": {"alg": "HS256"}}, b"hello", _empty_key()),
        "flattened JSON JWS signed",
    )


def test_general_json_verify_refuses_empty_key():
    value = general_token({"alg": "HS256"}, b"hello", EMPTY)
    assert_refused(lambda: jws.deserialize_json(value, _empty_key()), "general JSON JWS verified")


def test_general_json_sign_refuses_empty_key():
    assert_refused(
        lambda: jws.serialize_json([{"protected": {"alg": "HS256"}}], b"hello", _empty_key()),
        "general JSON JWS signed",
    )


def test_unencoded_payload_verify_refuses_empty_key():
    header = {"alg": "HS256", "b64": False, "crit": ["b64"]}
    token = b64_token(header, b"hello", EMPTY)
    assert_refused(lambda: jws.deserialize_compact(token, _empty_key()), "RFC 7797 JWS verified")


def test_mutated_key_refuses_empty_material():
    key = OctKey.import_key("rfc")
    key._raw_value = b""
    token = compact_token({"alg": "HS256"}, b"hello", EMPTY)
    assert_refused(lambda: jws.deserialize_compact(token, key), "key with cleared material")


def test_all_hmac_algorithms_refuse_empty_key():
    for alg, digest in (
        ("HS256", hashlib.sha256),
        ("HS384", hashlib.sha384),
        ("HS512", hashlib.sha512),
    ):
        token = compact_token({"alg": alg}, b"hello", EMPTY, digest)
        assert_refused(
            lambda alg=alg, token=token: jws.deserialize_compact(token, _empty_key(), algorithms=[alg]),
            f"{alg} verified with an empty key",
        )
