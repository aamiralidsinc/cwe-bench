"""Functional (2026-10-16): authenticated, correctly scoped stream writes keep
working. The run lives in the DEVELOPMENT environment; a client holding that
environment's API key writes into the run's realtime stream. The app has two
write routes for this: /realtime/v1/streams/<run>/<stream> (the one that was
anonymous) and /realtime/v1/streams/<run>/self/<stream> (API-key route). A fix
may remove the anonymous route or put authentication on it; either way at
least one authenticated write path must still accept the write, and the data
must reach the local Redis that backs the streams. A fix that disables stream
writes altogether fails here."""
import os
import tr


def test_authenticated_same_env_stream_write():
    assert tr.RUN and tr.DEV_KEY, "fixtures not provided by test.sh"
    stream = "legit" + os.urandom(6).hex()
    codes = []
    for target in ("self", None):
        r = tr.stream_write(tr.RUN, stream, data=b'{"hello":"world"}\n', token=tr.DEV_KEY,
                            target=target)
        codes.append(r["code"])
        if 200 <= r["code"] < 300:
            break
    assert 200 <= r["code"] < 300, (
        f"an authenticated same-environment stream write was refused on every write route "
        f"(HTTP {codes}); authorized stream writes must keep working."
    )
    assert tr.redis_keys_containing(stream), (
        "the authenticated stream write was answered with success but nothing reached the "
        "stream store")
