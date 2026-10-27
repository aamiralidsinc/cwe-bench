"""Refusal-tolerant assertions for pytest security tests (copy into tests/support/).

A security test that drives a hardened entry point must accept every secure outcome the instruction allows:
the call is refused (a client error, or one of the product's own refusal exceptions), or it completes and leaves
nothing unsafe behind. A crash is not a refusal: a server error (5xx) or an exception outside the declared
refusal types fails the test, so a fix that merely breaks the call is still caught (wrong-fix class
crash_as_refusal).

    from support.refusal import refused_or

    refused_or(lambda: client.post("/import", json=payload),
               ok=lambda resp: assert_no_secret(resp.text),
               refusals=(PermissionError, ValueError))
    assert_state_unchanged()          # side effects are checked after every outcome
"""

CLIENT_ERROR = range(400, 500)
STATUS_ATTRS = ("status_code", "status", "code", "statusCode")


def _status(obj):
    for name in STATUS_ATTRS:
        value = getattr(obj, name, None)
        if isinstance(value, int) and 100 <= value <= 599:
            return value
    return None


class Outcome:
    """What one call did: refused (with the reason) or returned a value."""

    def __init__(self, refused, value=None, reason=""):
        self.refused, self.value, self.reason = refused, value, reason

    def __repr__(self):
        return f"Outcome(refused={self.refused}, reason={self.reason!r})"


def attempt(call, refusals=()):
    """Run call() and classify the result.

    Refused when the call raises one of `refusals`, raises an exception that carries a 4xx status, or returns an
    object with a 4xx status. A 5xx status, or any other exception, propagates as a failure."""
    try:
        value = call()
    except AssertionError:
        raise
    except BaseException as exc:  # noqa: BLE001 - classified below, re-raised when not a refusal
        status = _status(exc)
        if status is not None:
            if status in CLIENT_ERROR:
                return Outcome(True, reason=f"{type(exc).__name__} {status}")
            raise
        if refusals and isinstance(exc, tuple(refusals)):
            return Outcome(True, reason=type(exc).__name__)
        raise
    status = _status(value)
    if status is not None and status in CLIENT_ERROR:
        return Outcome(True, value, reason=f"status {status}")
    if status is not None and status >= 500:
        raise AssertionError(f"server error {status}: a crash is not a refusal")
    return Outcome(False, value)


def refused_or(call, ok=None, refusals=()):
    """Pass when the call is refused, or when it completes and ok(value) holds (ok may assert or return a bool).
    Returns the Outcome so the test can check side effects either way."""
    out = attempt(call, refusals)
    if not out.refused and ok is not None:
        result = ok(out.value)
        if result is False:
            raise AssertionError("the call completed and its result is unsafe")
    return out


def must_refuse(call, refusals=()):
    """Pass only when the call is refused (for inputs the instruction says are never accepted)."""
    out = attempt(call, refusals)
    if not out.refused:
        raise AssertionError("expected a refusal (a client error or a refusal exception), the call completed")
    return out
