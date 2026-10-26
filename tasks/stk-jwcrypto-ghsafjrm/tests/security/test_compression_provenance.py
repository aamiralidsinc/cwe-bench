"""Compression may only be applied from header data the tag covers."""

import support

PLAIN_PROTECTED = {"alg": "A128KW", "enc": "A128GCM"}


def _run(token):
    support.reset_decompression()
    obj = support.jwe.JWE()
    obj.deserialize(token)
    refused = False
    try:
        obj.decrypt(support.make_key())
    except Exception:
        refused = True
    return obj, refused, support.decompressed_bytes()


def test_compression_declared_in_a_shared_unprotected_header_is_not_applied():
    token = support.json_token(
        PLAIN_PROTECTED,
        support.deflate_stream(support.LEGIT),
        unprotected={"zip": "DEF"},
    )
    obj, refused, produced = _run(token)

    assert produced == 0, (
        "compression was applied from an unauthenticated header")
    assert obj.plaintext != support.expanded(support.LEGIT), (
        "the expanded payload was produced")


def test_compression_declared_in_a_per_recipient_header_is_not_applied():
    token = support.json_token(
        PLAIN_PROTECTED,
        support.deflate_stream(support.LEGIT),
        recipient_headers=[{"zip": "DEF"}],
    )
    obj, refused, produced = _run(token)

    assert produced == 0, (
        "compression was applied from an unauthenticated header")
    assert obj.plaintext != support.expanded(support.LEGIT), (
        "the expanded payload was produced")
