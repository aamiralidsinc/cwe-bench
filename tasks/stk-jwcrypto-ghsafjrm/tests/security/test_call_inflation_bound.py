"""One decryption call must not inflate more than the allowance in total."""

import support


def test_many_recipients_do_not_multiply_the_inflation():
    piece = support.deflate_stream(support.LEGIT)
    token = support.json_token(
        {"alg": "A128KW", "enc": "A128GCM", "zip": "DEF"},
        piece,
        recipient_headers=[None] * 8,
    )
    support.reset_decompression()
    obj = support.jwe.JWE()
    obj.deserialize(token)
    try:
        obj.decrypt(support.make_key())
    except Exception:
        pass
    produced = support.decompressed_bytes()

    assert produced <= support.ALLOWANCE + support.OVERSHOOT, (
        "one call produced %d bytes of plaintext" % produced)
