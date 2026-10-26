"""Other reads the product performs must obey the same destination rule."""

from __future__ import annotations

import json

import pytest

from crewai_tools.rag.loaders.docs_site_loader import DocsSiteLoader
from crewai_tools.rag.loaders.pdf_loader import PDFLoader
from crewai_tools.rag.source_content import SourceContent
from crewai_tools.tools.jina_scrape_website_tool.jina_scrape_website_tool import (
    JinaScrapeWebsiteTool,
)
from crewai_tools.tools.serply_api_tool.serply_news_search_tool import (
    SerplyNewsSearchTool,
)

HTML = {"Content-Type": "text/html"}


def test_news_search_does_not_follow_result_link_to_internal_host(web, monkeypatch):
    monkeypatch.setenv("SERPLY_API_KEY", "test-key")
    api_url = "https://api.serply.io/v1/news/q=example"
    payload = {
        "entries": [
            {
                "link": "http://news.example/item",
                "title": "Example result",
                "source": {"title": "Example source"},
                "published": "2026-01-01",
            }
        ]
    }
    web.route(api_url, headers={"Content-Type": "application/json"}, body=json.dumps(payload))
    web.redirect("http://news.example/item", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body>INTERNAL-MARKER</body></html>",
    )

    with pytest.raises(Exception):
        SerplyNewsSearchTool()._run(search_query="example")

    assert web.calls_to("internal.example") == []


def test_jina_fallback_does_not_follow_redirect_to_internal_host(web):
    web.route(
        "https://r.jina.ai/http://public.example/start",
        status=503,
        headers={"Content-Type": "text/plain"},
        body="reader unavailable",
    )
    web.redirect("http://public.example/start", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body>INTERNAL-MARKER</body></html>",
    )

    tool = JinaScrapeWebsiteTool(website_url="http://public.example/start")
    with pytest.raises(Exception):
        tool._run()

    assert web.calls_to("internal.example") == []


def test_pdf_content_check_does_not_follow_redirect_to_internal_host(web):
    web.route(
        "http://public.example/doc.pdf",
        status=200,
        headers={"Content-Type": "application/pdf"},
        body=b"%PDF-1.4\nok\n%%EOF",
        method="GET",
    )
    web.redirect(
        "http://public.example/doc.pdf",
        "http://internal.example/admin",
        method="HEAD",
    )
    web.route(
        "http://internal.example/admin",
        headers={"Content-Type": "application/pdf"},
        body=b"%PDF-1.4\nINTERNAL-MARKER\n%%EOF",
    )

    with pytest.raises(Exception):
        PDFLoader().load(SourceContent("http://public.example/doc.pdf"))

    assert web.calls_to("internal.example") == []


def test_docs_loader_does_not_fetch_navigation_link_to_internal_host(web):
    page = (
        "<html><head><title>Guide</title></head><body>"
        '<nav><a href="/intro">Intro</a>'
        '<a href="//internal.example/admin">Admin</a></nav>'
        "<main><h1>Guide</h1><p>Body text</p></main></body></html>"
    )
    web.route("http://docs.example/guide", headers=HTML, body=page)
    web.route(
        "http://docs.example/intro",
        headers=HTML,
        body="<html><head><title>Intro</title></head><body><h1>Intro</h1></body></html>",
    )
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body><h1>Admin</h1>INTERNAL-MARKER</body></html>",
    )

    with pytest.raises(Exception):
        DocsSiteLoader().load(SourceContent("http://docs.example/guide"))

    assert web.calls_to("internal.example") == []
