"""A compressed token must not be allowed to inflate without bound.

This control suite covers only the reported route: an oversized compressed
payload refused by the public decryption entry points.
"""

import support

PROTECTED = {"alg": "A128KW", "enc": "A128GCM", "zip": "DEF"}


def _run(token, key=None):
    support.reset_decompression()
    obj = support.jwe.JWE()
    obj.deserialize(token)
    refused = False
    try:
        obj.decrypt(key or support.make_key())
    except Exception:
        refused = True
    return obj, refused, support.decompressed_bytes()


def test_oversized_compressed_payload_is_refused_and_bounded():
    token = support.compact(PROTECTED, support.deflate_stream(support.ATTACK))
    obj, refused, produced = _run(token)

    assert refused, "the oversized token was accepted"
    assert produced <= support.ALLOWANCE + support.OVERSHOOT, (
        "the decryption produced %d bytes" % produced)
    assert obj.plaintext != support.expanded(support.ATTACK), (
        "the oversized plaintext was returned")


def test_oversized_compressed_payload_in_json_serialization():
    token = support.json_token(
        PROTECTED, support.deflate_stream(support.ATTACK))
    obj, refused, produced = _run(token)

    assert refused, "the oversized token was accepted"
    assert produced <= support.ALLOWANCE + support.OVERSHOOT, (
        "the decryption produced %d bytes" % produced)
    assert obj.plaintext != support.expanded(support.ATTACK), (
        "the oversized plaintext was returned")


def test_oversized_compressed_payload_through_jwt():
    token = support.compact(PROTECTED, support.deflate_stream(support.ATTACK))
    support.reset_decompression()
    obj = support.jwt.JWT()
    obj.expected_type = "JWE"
    obj.deserialize(token)
    refused = False
    try:
        obj.validate(support.make_key())
    except Exception:
        refused = True
    produced = support.decompressed_bytes()

    assert refused, "the oversized token was accepted"
    assert produced <= support.ALLOWANCE + support.OVERSHOOT, (
        "the decryption produced %d bytes" % produced)


def test_oversized_compressed_payload_with_a_key_set():
    token = support.compact(PROTECTED, support.deflate_stream(support.ATTACK))
    keys = support.jwk.JWKSet()
    keys.add(support.make_key())
    obj, refused, produced = _run(token, keys)

    assert refused, "the oversized token was accepted"
    assert produced <= support.ALLOWANCE + support.OVERSHOOT, (
        "the decryption produced %d bytes" % produced)
    assert obj.plaintext != support.expanded(support.ATTACK), (
        "the oversized plaintext was returned")
