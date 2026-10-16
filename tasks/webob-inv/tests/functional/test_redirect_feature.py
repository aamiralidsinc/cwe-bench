"""Functional tests: legitimate redirect/resolution behaviour must be kept.

These assert that genuine, safe uses of the redirect and URL-resolution
features keep working: an application may still redirect to an explicitly
absolute off-site URL (e.g. an identity provider or a CDN), to an absolute
same-host path, or to a reference resolved relative to the current request
(which must resolve exactly as it does today, including an explicitly
protocol-relative reference).

A fix that kills the open redirect by disabling or over-restricting the
feature (for example by forcing every redirect onto the request's own host)
breaks at least one of these.
"""
from urllib.parse import urlsplit

import pytest

from webob import Request, Response
from webob.exc import HTTPFound

REQUEST_PATH = "/app/page"


def _request():
    return Request.blank(REQUEST_PATH)


def _response_location(raw_location):
    resp = Response(status=302)
    resp.location = raw_location
    return _request().get_response(resp).location


def _httpexception_location(raw_location):
    environ = _request().environ
    captured = {}

    def start_response(status, headers, exc_info=None):
        captured["headers"] = headers

    HTTPFound(location=raw_location)(environ, start_response)
    return dict(captured["headers"]).get("Location")


# --- Response Location header ------------------------------------------------

def test_response_absolute_offsite_url_is_preserved():
    # Redirecting to an explicitly absolute URL on another host is a normal,
    # intended feature (SSO, payment provider, CDN) and must be preserved.
    loc = _response_location("https://other.example.com/landing")
    parts = urlsplit(loc)
    assert parts.hostname == "other.example.com"
    assert parts.scheme == "https"


def test_response_absolute_same_host_path():
    loc = _response_location("/dashboard")
    parts = urlsplit(loc)
    assert parts.hostname == "localhost"
    assert parts.path == "/dashboard"


def test_response_relative_reference_resolves_under_current_dir():
    loc = _response_location("page2")
    parts = urlsplit(loc)
    assert parts.hostname == "localhost"
    assert parts.path == "/app/page2"


def test_response_protocol_relative_stays_on_host():
    # A protocol-relative value is neutralised (kept on-host), not dropped.
    loc = _response_location("//cdn.example.com/asset.js")
    parts = urlsplit(loc)
    assert parts.hostname == "localhost"
    assert "cdn.example.com" in loc  # the path is retained, just made safe


# --- HTTP redirect exception (HTTPFound) ------------------------------------

def test_exception_absolute_offsite_url_is_preserved():
    loc = _httpexception_location("https://sso.example.org/auth")
    parts = urlsplit(loc)
    assert parts.hostname == "sso.example.org"
    assert parts.scheme == "https"


def test_exception_relative_location_resolves_on_host():
    loc = _httpexception_location("/login")
    parts = urlsplit(loc)
    assert parts.hostname == "localhost"
    assert parts.path == "/login"


# --- Request-relative URL resolution ----------------------------------------

def test_relative_url_resolves_under_current_dir():
    loc = _request().relative_url("other")
    parts = urlsplit(loc)
    assert parts.hostname == "localhost"
    assert parts.path == "/app/other"


def test_relative_url_to_application_root():
    loc = _request().relative_url("sub", to_application=True)
    parts = urlsplit(loc)
    assert parts.hostname == "localhost"
    assert parts.path == "/sub"


def test_relative_url_explicit_protocol_relative_unchanged():
    # Added 2026-10-16. An explicitly protocol-relative reference (no leading
    # character) is outside the same-site guarantee, and resolution relative to
    # the request must work "exactly as it does today": standard resolution,
    # where the reference names its own host.
    loc = _request().relative_url("//other.example.com/x")
    parts = urlsplit(loc)
    assert parts.hostname == "other.example.com"
    assert parts.path == "/x"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
