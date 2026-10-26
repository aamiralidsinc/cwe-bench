"""Credentials must not travel to a different origin when a read is redirected."""

from __future__ import annotations

from crewai_tools.rag.loaders.webpage_loader import WebPageLoader
from crewai_tools.rag.source_content import SourceContent
from crewai_tools.tools.scrape_website_tool.scrape_website_tool import (
    ScrapeWebsiteTool,
)

API_KEY = "API-KEY-SECRET"
TOKEN = "TOKEN-SECRET"
COOKIE = "COOKIE-SECRET"
BEARER = "BEARER-SECRET"

HTML = {"Content-Type": "text/html"}


def _second_origin_text(web) -> str:
    calls = web.calls_to("cdn.example")
    assert len(calls) == 1, f"expected the public redirect to be followed: {web.urls()}"
    return calls[0].header_text()


def test_scraper_does_not_forward_api_key_header_across_origins(web):
    web.redirect("http://public.example/start", "http://cdn.example/final")
    web.route(
        "http://cdn.example/final",
        headers=HTML,
        body="<html><body>PUBLIC-CONTENT</body></html>",
    )
    tool = ScrapeWebsiteTool(website_url="http://public.example/start")

    original = {
        "User-Agent": "crew-test",
        "Authorization": f"Bearer {BEARER}",
        "X-Api-Key": API_KEY,
        "X-CrewAI-Token": TOKEN,
    }
    tool.headers = original
    result = tool._run()

    assert "PUBLIC-CONTENT" in str(result)
    forwarded = _second_origin_text(web)
    assert API_KEY not in forwarded
    assert TOKEN not in forwarded
    assert BEARER not in forwarded


def test_scraper_does_not_forward_cookie_across_origins(web, monkeypatch):
    monkeypatch.setenv("SESSION_VALUE", COOKIE)
    web.redirect("http://public.example/start", "http://cdn.example/final")
    web.route(
        "http://cdn.example/final",
        headers=HTML,
        body="<html><body>PUBLIC-CONTENT</body></html>",
    )
    tool = ScrapeWebsiteTool(
        website_url="http://public.example/start",
        cookies={"name": "session", "value": "SESSION_VALUE"},
    )

    result = tool._run()

    assert "PUBLIC-CONTENT" in str(result)
    assert COOKIE not in _second_origin_text(web)


def test_loader_does_not_forward_api_key_header_across_origins(web):
    web.redirect("http://public.example/page", "http://cdn.example/final")
    web.route(
        "http://cdn.example/final",
        headers=HTML,
        body="<html><body>PUBLIC-CONTENT</body></html>",
    )

    result = WebPageLoader().load(
        SourceContent("http://public.example/page"),
        headers={"User-Agent": "crew-test", "X-Api-Key": API_KEY},
    )

    assert "PUBLIC-CONTENT" in result.content
    forwarded = _second_origin_text(web)
    assert API_KEY not in forwarded
