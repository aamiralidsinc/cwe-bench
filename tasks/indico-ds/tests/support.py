"""Shared helpers for the behavioural suites.

Copied into the workspace at grade time (the suites run with this directory on
PYTHONPATH). Product imports happen inside the helpers/tests so that the
application fixtures are already in place.
"""

import json

#: A target that would execute code when opened. Never executed by the tests.
BAD_URL = 'javascript:alert(1)'
#: A code-executing target placed inside rich text as an attribute value.
BAD_ATTR = 'onerror="alert(1)"'
BAD_HTML = f'<img src="x" {BAD_ATTR}>'

#: Ordinary web addresses that must keep working.
GOOD_URL = 'https://example.com/indico-marker'
GOOD_URL2 = 'http://example.com/another-marker'

CSRF_TOKEN = 'indico-test-csrf-0123456789abcdef'
LOCATION_DATA = json.dumps({'inheriting': False, 'address': '', 'room_id': None, 'venue_id': None})


def assert_clean_refusal(response):
    """A refusal may re-show the form, redirect or answer 4xx - never a server error."""
    assert response.status_code < 500, (
        f'expected a clean refusal, got server error {response.status_code}: {response.text[:400]}'
    )


def assert_html_is_inert(html):
    """No script-bearing markup or code-executing attribute/link may be delivered."""
    lowered = (html or '').lower()
    assert '<script' not in lowered, f'script markup was delivered: {html!r}'
    assert 'onerror' not in lowered, f'event-handler attribute was delivered: {html!r}'
    assert 'javascript:' not in lowered, f'code-executing link target was delivered: {html!r}'


def assert_link_is_safe(url):
    """A stored link target must not use a code-executing scheme."""
    assert 'javascript:' not in (url or '').lower(), f'a code-executing link target was kept: {url!r}'


def attachment_link_urls():
    from indico.modules.attachments.models.attachments import Attachment
    return [a.link_url for a in Attachment.query.all() if a.link_url]


def menu_link_urls(event):
    from indico.modules.events.layout.models.menu import MenuEntry
    return [e.link_url for e in MenuEntry.query.with_parent(event) if e.link_url]
