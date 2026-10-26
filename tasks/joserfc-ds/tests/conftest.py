"""Helpers for the hidden suites.

Everything needed to build an attack token is computed here with the standard library
only, so a hardened signing path in the product cannot break the tests' own bookkeeping.
The expected key material for the plain-secret route is the fixed 256-bit value the
implementation produces from an empty secret.
"""
import base64
import hashlib
import hmac
import json


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _segment(value) -> str:
    if isinstance(value, bytes):
        return b64(value)
    return b64(json.dumps(value, separators=(",", ":")).encode())


def compact_token(header, payload, key: bytes, digest=hashlib.sha256) -> str:
    signing_input = (_segment(header) + "." + _segment(payload)).encode()
    signature = hmac.new(key, signing_input, digest).digest()
    return signing_input.decode() + "." + b64(signature)


def flattened_token(header, payload, key: bytes, digest=hashlib.sha256) -> dict:
    protected = _segment(header)
    payload_segment = _segment(payload)
    signing_input = (protected + "." + payload_segment).encode()
    return {
        "payload": payload_segment,
        "protected": protected,
        "signature": b64(hmac.new(key, signing_input, digest).digest()),
    }


def general_token(header, payload, key: bytes, digest=hashlib.sha256) -> dict:
    protected = _segment(header)
    payload_segment = _segment(payload)
    signing_input = (protected + "." + payload_segment).encode()
    signature = b64(hmac.new(key, signing_input, digest).digest())
    return {"payload": payload_segment, "signatures": [{"protected": protected, "signature": signature}]}


def b64_token(header, payload, key: bytes, digest=hashlib.sha256) -> str:
    """RFC 7797 unencoded-payload compact serialization (URL-safe payload)."""
    protected = _segment(header)
    signing_input = protected.encode() + b"." + payload
    return signing_input.decode() + "." + b64(hmac.new(key, signing_input, digest).digest())


def refuses(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


def assert_refused(fn, what: str = "") -> None:
    assert refuses(fn), f"operation was accepted instead of refused: {what}"


def assert_works(fn, what: str = ""):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - the functional suite wants the failure visible
        raise AssertionError(f"legitimate operation failed: {what}: {type(exc).__name__}: {exc}") from exc
