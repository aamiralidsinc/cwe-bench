"""Offline fake network for the crewai-tools URL-reading tests.

Two patches make every requests-based read observable without opening a socket:

* ``socket.getaddrinfo`` is replaced by a small host table (public hosts resolve to public
  addresses, internal hosts to private / link-local addresses). This is what the product's own
  URL validator consults.
* ``requests.adapters.HTTPAdapter.send`` is replaced by a fake transport that records
  (method, URL, prepared headers) and answers from a per-test route table. Every requests entry
  point funnels through the adapter, including requests.get, Session.get, requests.head and
  requests.request, so the tests observe the wire rather than any particular helper.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any
from urllib.parse import urlsplit

import pytest
import requests
from requests.structures import CaseInsensitiveDict


PUBLIC_HOSTS = {
    "example.com": "93.184.216.34",
    "api.example.com": "93.184.216.34",
    "public.example": "93.184.216.34",
    "docs.example": "93.184.216.35",
    "cdn.example": "93.184.216.36",
    "news.example": "93.184.216.37",
    "api.serply.io": "93.184.216.38",
    "r.jina.ai": "93.184.216.39",
}

INTERNAL_HOSTS = {
    "internal.example": "10.20.30.40",
    "vault.example": "192.168.10.7",
    "metadata.example": "169.254.169.254",
}

_FALLBACK_PUBLIC = "93.184.216.90"


def _fake_getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> list[tuple[Any, ...]]:
    name = host.decode() if isinstance(host, bytes) else str(host)
    address = INTERNAL_HOSTS.get(name) or PUBLIC_HOSTS.get(name)
    if address is None:
        address = name  # an IP literal (e.g. 169.254.169.254) resolves to itself
        try:
            socket.inet_pton(socket.AF_INET, address)
        except OSError:
            address = _FALLBACK_PUBLIC
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port or 443))]


@dataclass
class Call:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)

    def header_text(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in self.headers.items())


class FakeWeb:
    """Per-test route table and request log for the fake transport."""

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], tuple[int, dict[str, str], bytes]] = {}
        self.calls: list[Call] = []

    def route(
        self,
        url: str,
        status: int = 200,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | str = b"",
        method: str | None = None,
    ) -> None:
        payload = body.encode() if isinstance(body, str) else body
        key = (method.upper() if method else "*", url)
        self._routes[key] = (status, dict(headers or {}), payload)

    def redirect(self, url: str, location: str, status: int = 302, method: str | None = None) -> None:
        self.route(url, status, headers={"Location": location}, method=method)

    def answer(self, method: str, url: str) -> tuple[int, dict[str, str], bytes]:
        return (
            self._routes.get((method.upper(), url))
            or self._routes.get(("*", url))
            or (404, {"Content-Type": "text/plain"}, b"not found")
        )

    def urls(self) -> list[str]:
        return [call.url for call in self.calls]

    def calls_to(self, host: str) -> list[Call]:
        return [call for call in self.calls if urlsplit(call.url).hostname == host]


@pytest.fixture(autouse=True)
def offline_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo)


@pytest.fixture
def web(monkeypatch: pytest.MonkeyPatch) -> FakeWeb:
    fake = FakeWeb()
    def send(
        self: requests.adapters.HTTPAdapter,
        request: requests.PreparedRequest,
        **kwargs: Any,
    ) -> requests.Response:
        fake.calls.append(
            Call(request.method or "", request.url or "", dict(request.headers))
        )
        status, headers, body = fake.answer(request.method or "", request.url or "")
        response = requests.Response()
        response.status_code = status
        response.url = request.url
        response.headers = CaseInsensitiveDict(headers)
        response._content = body
        response.raw = BytesIO(body)
        response.encoding = "utf-8"
        response.request = request
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    return fake
