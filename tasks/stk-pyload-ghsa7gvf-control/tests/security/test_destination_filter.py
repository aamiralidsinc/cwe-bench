"""The download of a link a user supplies must not reach a destination that
is not globally routable."""
import pytest

from support import harness


def _refused(env, url, name, target=None):
    env.set_proxy(None)
    env.reset_downloads()
    env.try_download(url, name=name)
    if target is not None:
        assert target.hits == [], "the private service was contacted"
    assert not env.payload_downloaded(), "content served by the private service was kept"


def test_loopback_destination_is_refused(env):
    target = harness.Target()
    try:
        _refused(env, "http://127.0.0.1:{}/payload.bin".format(target.port), "c1", target)
    finally:
        target.close()


def test_loopback_name_destination_is_refused(env):
    target = harness.Target()
    try:
        _refused(env, "http://localhost:{}/payload.bin".format(target.port), "c2", target)
    finally:
        target.close()


def test_alternate_loopback_destination_is_refused(env):
    target = harness.Target(host="127.0.0.2")
    try:
        _refused(env, "http://127.0.0.2:{}/payload.bin".format(target.port), "c3", target)
    finally:
        target.close()


def test_loopback_v6_destination_is_refused(env):
    target = harness.Target(host="::1")
    try:
        _refused(env, "http://[::1]:{}/payload.bin".format(target.port), "c4", target)
    finally:
        target.close()
