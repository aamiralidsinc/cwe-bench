"""Shared helpers for the hidden suites.

Tokens are built with the product's own algorithm primitives and every check
drives a public decryption entry point.  The decompression primitive is
counted before the product is imported, so the suites measure what a fix
actually inflates rather than how it happens to be written.
"""
import zlib as _zlib

_orig_decompress = _zlib.decompress
_orig_decompressobj = _zlib.decompressobj
_totals = {"bytes": 0, "calls": 0}


def _record(size):
    _totals["bytes"] += size
    _totals["calls"] += 1


def _decompress(data, *args, **kwargs):
    out = _orig_decompress(data, *args, **kwargs)
    _record(len(out))
    return out


class _Decompressor:
    """Counts every byte an incremental decompression produces."""

    def __init__(self, *args, **kwargs):
        self._inner = _orig_decompressobj(*args, **kwargs)

    def decompress(self, data, max_length=0):
        out = self._inner.decompress(data, max_length)
        _record(len(out))
        return out

    def flush(self, *args, **kwargs):
        out = self._inner.flush(*args, **kwargs)
        _record(len(out))
        return out

    def __getattr__(self, name):
        return getattr(self._inner, name)


def _decompressobj(*args, **kwargs):
    return _Decompressor(*args, **kwargs)


_zlib.decompress = _decompress
_zlib.decompressobj = _decompressobj


def reset_decompression():
    _totals["bytes"] = 0
    _totals["calls"] = 0


def decompressed_bytes():
    return _totals["bytes"]


def decompression_calls():
    return _totals["calls"]


from jwcrypto import jwe, jwk, jwa, jwt  # noqa: E402
from jwcrypto.common import base64url_encode, json_encode  # noqa: E402

ALLOWANCE = 8 * 1024 * 1024
OVERSHOOT = 1 * 1024 * 1024
ATTACK = ALLOWANCE + 8 * 1024 * 1024
LEGIT = 2 * 1024 * 1024

_CEK = b"C" * 16


def make_key():
    return jwk.JWK(kty="oct", k=base64url_encode(b"A" * 16))


def deflate_stream(total):
    """A raw DEFLATE stream whose expansion is `total` bytes, built without
    ever allocating the expansion."""
    compressor = _zlib.compressobj(9, _zlib.DEFLATED, -_zlib.MAX_WBITS)
    pieces = []
    done = 0
    block = b"\x00" * (1 << 20)
    while done < total:
        pieces.append(compressor.compress(block))
        done += len(block)
    pieces.append(compressor.flush())
    return b"".join(pieces)


def expanded(total):
    return b"\x00" * total


def _seal(protected, content):
    protected_json = json_encode(protected)
    aad = base64url_encode(protected_json).encode()
    enc = jwa.JWA.encryption_alg(protected["enc"])
    km = jwa.JWA.keymgmt_alg(protected["alg"])
    iv, ciphertext, tag = enc.encrypt(_CEK, aad, content)
    return protected_json, enc, km, iv, ciphertext, tag


def _wrap(km, enc, header):
    return km.wrap(make_key(), enc.wrap_key_size, _CEK, header)["ek"]


def compact(protected, content):
    protected_json, enc, km, iv, ciphertext, tag = _seal(protected, content)
    encrypted_key = _wrap(km, enc, protected)
    return ".".join(
        base64url_encode(value)
        for value in (protected_json, encrypted_key, iv, ciphertext, tag)
    )


def json_token(protected, content, unprotected=None, recipient_headers=None):
    protected_json, enc, km, iv, ciphertext, tag = _seal(protected, content)
    token = {
        "protected": base64url_encode(protected_json),
        "iv": base64url_encode(iv),
        "ciphertext": base64url_encode(ciphertext),
        "tag": base64url_encode(tag),
    }
    if unprotected is not None:
        token["unprotected"] = unprotected
    if recipient_headers is None:
        token["encrypted_key"] = base64url_encode(_wrap(km, enc, protected))
    else:
        recipients = []
        for extra in recipient_headers:
            header = dict(protected)
            if extra:
                header.update(extra)
            record = {"encrypted_key": base64url_encode(_wrap(km, enc, header))}
            if extra:
                record["header"] = extra
            recipients.append(record)
        token["recipients"] = recipients
    return json_encode(token)


def decrypt_jwe(token, key=None):
    obj = jwe.JWE()
    obj.deserialize(token)
    obj.decrypt(key or make_key())
    return obj


def decrypt_jwt(token, key=None):
    obj = jwt.JWT()
    obj.expected_type = "JWE"
    obj.deserialize(token, key or make_key())
    return obj
