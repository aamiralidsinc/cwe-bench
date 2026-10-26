"""Decide whether a redirect destination leaves the notebook server.

The checks below follow how a browser resolves a Location value: backslashes
are treated as slashes, and a scheme-relative prefix may be followed by any run
of extra slashes before the authority begins.
"""

from urllib.parse import urlparse

_LOCAL_NAMES = ("localhost", "127.0.0.1", "::1", "[::1]")


def _authority_parts(value):
    authority = value.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in authority:
        authority = authority.rsplit("@", 1)[1]
    if authority.startswith("["):
        end = authority.find("]")
        host = authority[: end + 1]
        rest = authority[end + 1 :]
        port = rest[1:] if rest.startswith(":") else ""
        return host, port
    host, _, port = authority.partition(":")
    return host, port


def _is_local(host):
    return (host or "").lower() in _LOCAL_NAMES


def points_off_origin(location, port):
    """True when a browser following ``location`` would leave this server."""
    if not location:
        return False
    resolved = location.replace("\\", "/")
    parsed = urlparse(resolved)
    if parsed.scheme or parsed.netloc:
        host = parsed.hostname
        if host is None:
            return bool(parsed.scheme)
        if _is_local(host):
            return parsed.port not in (None, port)
        return True
    if resolved.startswith("//"):
        host, port_text = _authority_parts(resolved[2:].lstrip("/"))
        if _is_local(host) or host == "":
            return bool(port_text) and port_text.isdigit() and int(port_text) != port
        return True
    return False


def assert_refused_or_in_server(response, port):
    """A response to a rejected destination: a client error, or an in-server redirect."""
    status = response.status_code
    if 400 <= status < 500:
        return
    assert 300 <= status < 400, "not a refusal and not a redirect (status %s)" % status
    location = response.headers.get("Location")
    assert location, "redirect response without a destination"
    assert not points_off_origin(location, port), (
        "redirect leaves the server: %r" % location
    )


def assert_raw_refused_or_in_server(status, location, port):
    """The same decision for a response read with http.client."""
    if 400 <= status < 500:
        return
    assert 300 <= status < 400, "not a refusal and not a redirect (status %s)" % status
    assert location, "redirect response without a destination"
    assert not points_off_origin(location, port), (
        "redirect leaves the server: %r" % location
    )
