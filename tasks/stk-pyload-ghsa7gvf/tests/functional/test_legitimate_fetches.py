"""Legitimate fetching keeps working: public destinations, public redirects,
IPv6-only public destinations, a configured proxy and local container files."""
import os
import socket

import pytest

from support import harness


def _require_name(name):
    try:
        socket.getaddrinfo(name, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        pytest.fail("the test environment is missing the name {}".format(name))


def _page():
    return '<a href="{}">x</a>'.format(harness.GOOD_LINK).encode()


def test_page_fetch_through_proxy_still_works(env):
    proxy = harness.Proxy()
    proxy.routes[(harness.PUBLIC_IP, "/page.html")] = {
        "body": _page(),
        "headers": {"Content-Type": "text/html"},
    }
    try:
        env.set_proxy(proxy)
        result = env.parse("http://{}/page.html".format(harness.PUBLIC_IP))
        assert harness.GOOD_LINK in harness.links_of(result)
    finally:
        proxy.close()


def test_link_extraction_from_supplied_html_still_works(env):
    env.set_proxy(None)
    result = env.parse_html('<a href="{}">x</a>'.format(harness.GOOD_LINK))
    assert harness.GOOD_LINK in harness.links_of(result)


def test_redirect_between_public_destinations_still_works(env):
    proxy = harness.Proxy()
    proxy.routes[(harness.PUBLIC_IP, "/start.html")] = {
        "status": 302,
        "headers": {"Location": "http://{}/final.html".format(harness.PUBLIC_IP2)},
    }
    proxy.routes[(harness.PUBLIC_IP2, "/final.html")] = {
        "body": _page(),
        "headers": {"Content-Type": "text/html"},
    }
    try:
        env.set_proxy(proxy)
        result = env.parse("http://{}/start.html".format(harness.PUBLIC_IP))
        assert harness.GOOD_LINK in harness.links_of(result)
    finally:
        proxy.close()


def test_ipv6_only_public_destination_still_works(env):
    _require_name(harness.PUBLIC_V6_NAME)
    proxy = harness.Proxy()
    proxy.routes[(harness.PUBLIC_V6_NAME, "/list.html")] = {
        "body": _page(),
        "headers": {"Content-Type": "text/html"},
    }
    try:
        env.set_proxy(proxy)
        env.set_ipv6(True)
        result = env.parse("http://{}/list.html".format(harness.PUBLIC_V6_NAME))
        assert harness.GOOD_LINK in harness.links_of(result)
    finally:
        proxy.close()


def test_local_container_file_still_processed(env):
    env.set_proxy(None)
    path = os.path.join(env.base, "links.txt")
    with open(path, "w") as handle:
        handle.write("http://example.com/one\nhttp://example.com/two\n")

    packages = env.process_local_container(path)

    links = [link for _name, package_links, _folder in packages for link in package_links]
    assert "http://example.com/one" in links
    assert "http://example.com/two" in links
