"""CWE-306 missing authentication: the realtime stream WRITE endpoint accepts
data for a run identified only by its (guessable) friendlyId, with no
authentication. Anyone can inject arbitrary data into any run's realtime
stream, including production.

Exploit entry point: POST /realtime/v1/streams/<runFriendlyId>/<streamId>
with no Authorization header. Vulnerable: accepted (HTTP 200). Fixed: the
anonymous write is refused with any 4xx (e.g. 401/403 when the route now
requires authorization, or 404/405 when the anonymous route was removed); how
it is refused is the fix's choice.

2026-10-16: also a valid API key of a DIFFERENT environment of the same
project (the run lives in DEVELOPMENT; the PRODUCTION key is used). The
instruction asks for authenticated, correctly scoped access, so a fix that
only demands some credential, but does not tie it to the run's environment,
must still fail. Each attack writes to a fresh stream name, and the local
Redis that backs the streams must hold nothing under that name afterwards.
"""
import os
import tr


def test_unauthenticated_stream_write_blocked():
    assert tr.RUN, "fixtures not provided by test.sh"
    stream = "anon" + os.urandom(6).hex()
    r = tr.stream_write(tr.RUN, stream, data=b"INJECTED_BY_ATTACKER")
    assert r["code"] != 200, (
        f"an unauthenticated client wrote to run {tr.RUN}'s realtime stream "
        f"(HTTP {r['code']}); unauthenticated stream writes must be refused."
    )
    assert 400 <= r["code"] < 500, (
        f"the anonymous stream write was not refused with a 4xx (HTTP {r['code']})"
    )
    assert not tr.redis_keys_containing(stream), (
        "the anonymous write left data in the run's stream store")


def test_other_environment_key_stream_write_blocked():
    assert tr.RUN and tr.PROD_KEY, "fixtures not provided by test.sh"
    stream = "xenv" + os.urandom(6).hex()
    r = tr.stream_write(tr.RUN, stream, data=b"INJECTED_CROSS_ENV", token=tr.PROD_KEY)
    assert not (200 <= r["code"] < 300), (
        f"a PRODUCTION-environment key wrote into a DEVELOPMENT run's realtime stream "
        f"(HTTP {r['code']}); stream writes must be scoped to the run's own environment."
    )
    assert 400 <= r["code"] < 500, (
        f"the cross-environment stream write was not refused with a 4xx (HTTP {r['code']})"
    )
    assert not tr.redis_keys_containing(stream), (
        "the cross-environment write left data in the run's stream store")
