"""Legitimate encryption and decryption keep working."""

import json

import support


def _roundtrip(payload, protected):
    token = support.jwe.JWE(
        payload, protected=protected, recipient=support.make_key()
    ).serialize(compact=True)
    obj = support.jwe.JWE()
    obj.deserialize(token)
    obj.decrypt(support.make_key())
    return obj.plaintext


def test_compressed_payload_within_the_allowance_round_trips():
    payload = b"\x00" * support.LEGIT
    assert _roundtrip(
        payload, {"alg": "A128KW", "enc": "A128GCM", "zip": "DEF"}
    ) == payload


def test_uncompressed_payload_larger_than_the_allowance_round_trips():
    payload = b"u" * (support.ALLOWANCE + 4 * 1024 * 1024)
    assert _roundtrip(payload, {"alg": "A128KW", "enc": "A128GCM"}) == payload


def test_multi_recipient_token_decrypts_for_each_key():
    first = support.jwk.JWK.generate(kty="oct", size=128)
    second = support.jwk.JWK.generate(kty="oct", size=128)
    token = support.jwe.JWE(
        b"shared-secret",
        protected={"alg": "A128KW", "enc": "A128GCM"},
        recipient=first,
    )
    token.add_recipient(second)
    raw = token.serialize()
    for key in (first, second):
        obj = support.jwe.JWE()
        obj.deserialize(raw)
        obj.decrypt(key)
        assert obj.plaintext == b"shared-secret"


def test_algorithm_headers_in_a_shared_unprotected_header_still_decrypt():
    payload = b"header-placement"
    token = support.jwe.JWE(
        payload,
        protected={"typ": "JWE"},
        unprotected={"alg": "A128KW", "enc": "A128GCM"},
        recipient=support.make_key(),
    ).serialize()
    obj = support.jwe.JWE()
    obj.deserialize(token)
    obj.decrypt(support.make_key())
    assert obj.plaintext == payload


def test_encrypted_jwt_round_trips():
    token = support.jwt.JWT(
        header={"alg": "A128KW", "enc": "A128GCM", "zip": "DEF"},
        claims={"sub": "legitimate"},
    )
    token.make_encrypted_token(support.make_key())
    raw = token.serialize()
    obj = support.jwt.JWT()
    obj.expected_type = "JWE"
    obj.deserialize(raw, support.make_key())
    assert json.loads(obj.claims)["sub"] == "legitimate"


def test_plain_compact_token_round_trips():
    assert _roundtrip(
        b"plain payload", {"alg": "A128KW", "enc": "A128GCM"}
    ) == b"plain payload"
