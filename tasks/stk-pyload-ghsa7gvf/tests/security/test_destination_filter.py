"""The product must not fetch a user-supplied destination that is not globally
routable, however that destination is reached and whichever address family it
resolves to."""
import os
import socket

import pytest

from support import harness


def _require_name(name):
    try:
        socket.getaddrinfo(name, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        pytest.fail("the test environment is missing the name {}".format(name))


def test_download_from_private_address_is_refused(env):
    target = harness.Target()
    try:
        env.set_proxy(None)
        env.reset_downloads()

        env.try_download(
            "http://127.0.0.1:{}/t1/payload.bin".format(target.port), name="t1"
        )

        assert target.hits == [], "the private service was contacted"
        assert not env.payload_downloaded(), "content served by the private service was kept"
    finally:
        target.close()


def test_private_page_fetch_for_link_extraction_is_refused(env):
    page = '<a href="{}">x</a>'.format(harness.SECRET_LINK).encode()
    target = harness.Target(body=page, content_type="text/html")
    try:
        env.set_proxy(None)

        result, _error = env.try_parse(
            "http://127.0.0.1:{}/t4/page.html".format(target.port)
        )

        assert target.hits == [], "the private service was contacted"
        assert harness.SECRET_LINK not in harness.links_of(result)
    finally:
        target.close()


def test_redirect_hop_to_private_address_is_refused(env):
    target = harness.Target()
    proxy = harness.Proxy()
    proxy.routes[(harness.PUBLIC_IP, "/t2/start.bin")] = {
        "status": 302,
        "headers": {"Location": "http://127.0.0.1:{}/t2/secret.bin".format(target.port)},
    }
    proxy.forward[("127.0.0.1", "/t2/secret.bin")] = target
    try:
        env.set_proxy(proxy)
        env.reset_downloads()

        env.try_download(
            "http://{}/t2/start.bin".format(harness.PUBLIC_IP), name="t2"
        )

        assert "127.0.0.1" not in proxy.hosts(), "the redirect target was requested"
        assert target.hits == [], "the private service was contacted"
        assert not env.payload_downloaded(), "content served by the private service was kept"
    finally:
        proxy.close()
        target.close()


def test_private_destination_through_proxy_is_refused(env):
    target = harness.Target()
    proxy = harness.Proxy()
    proxy.forward[("127.0.0.1", "/t8/secret.bin")] = target
    try:
        env.set_proxy(proxy)
        env.reset_downloads()

        env.try_download(
            "http://127.0.0.1:{}/t8/secret.bin".format(target.port), name="t8"
        )

        assert "127.0.0.1" not in proxy.hosts(), "the private destination was sent on"
        assert target.hits == [], "the private service was contacted"
        assert not env.payload_downloaded(), "content served by the private service was kept"
    finally:
        proxy.close()
        target.close()


def test_ipv6_only_private_destination_is_refused(env):
    _require_name(harness.PRIVATE_V6_NAME)
    target = harness.Target()
    proxy = harness.Proxy()
    proxy.forward[(harness.PRIVATE_V6_NAME, "/t7/secret.bin")] = target
    try:
        env.set_proxy(proxy)
        env.set_ipv6(True)
        env.reset_downloads()

        env.try_download(
            "http://{}/t7/secret.bin".format(harness.PRIVATE_V6_NAME), name="t7"
        )

        assert harness.PRIVATE_V6_NAME not in proxy.hosts(), "the private destination was sent on"
        assert target.hits == [], "the private service was contacted"
        assert not env.payload_downloaded(), "content served by the private service was kept"
    finally:
        proxy.close()
        target.close()
