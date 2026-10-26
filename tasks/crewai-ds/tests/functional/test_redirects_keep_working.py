"""Legitimate redirects and same-origin credential use keep working."""

from __future__ import annotations

from crewai_tools.rag.loaders.csv_loader import CSVLoader
from crewai_tools.rag.loaders.webpage_loader import WebPageLoader
from crewai_tools.rag.source_content import SourceContent
from crewai_tools.tools.scrape_element_from_website.scrape_element_from_website import (
    ScrapeElementFromWebsiteTool,
)
from crewai_tools.tools.scrape_website_tool.scrape_website_tool import (
    ScrapeWebsiteTool,
)

HTML = {"Content-Type": "text/html"}


def test_web_page_scraper_follows_relative_redirect(web):
    web.redirect("http://public.example/start", "/final")
    web.route(
        "http://public.example/final",
        headers=HTML,
        body="<html><body>Hello Page</body></html>",
    )

    result = ScrapeWebsiteTool(website_url="http://public.example/start")._run()

    assert "Hello Page" in result


def test_web_page_scraper_follows_public_cross_origin_redirect(web):
    web.redirect("http://public.example/start", "http://cdn.example/final")
    web.route(
        "http://cdn.example/final",
        headers=HTML,
        body="<html><body>Cross Origin Page</body></html>",
    )

    result = ScrapeWebsiteTool(website_url="http://public.example/start")._run()

    assert "Cross Origin Page" in result


def test_web_page_scraper_follows_multi_hop_public_redirect(web):
    web.redirect("http://public.example/start", "http://cdn.example/hop")
    web.redirect("http://cdn.example/hop", "http://news.example/final")
    web.route(
        "http://news.example/final",
        headers=HTML,
        body="<html><body>Final Page</body></html>",
    )

    result = ScrapeWebsiteTool(website_url="http://public.example/start")._run()

    assert "Final Page" in result


def test_element_scraper_follows_redirect_and_selects_element(web):
    web.redirect("http://public.example/start", "http://public.example/next")
    web.route(
        "http://public.example/next",
        headers=HTML,
        body='<html><body><div class="note">Picked Text</div></body></html>',
    )
    tool = ScrapeElementFromWebsiteTool(
        website_url="http://public.example/start", css_element="div.note"
    )

    result = tool._run()

    assert "Picked Text" in result


def test_web_page_loader_follows_public_redirect(web):
    web.redirect("http://public.example/page", "http://public.example/final")
    web.route(
        "http://public.example/final",
        headers=HTML,
        body="<html><head><title>Loaded</title></head><body>Loader Body</body></html>",
    )

    result = WebPageLoader().load(SourceContent("http://public.example/page"))

    assert "Loader Body" in result.content


def test_csv_loader_reads_public_url(web):
    web.route(
        "http://public.example/data.csv",
        headers={"Content-Type": "text/csv"},
        body="name,value\nalpha,1\nbeta,2\n",
    )

    result = CSVLoader().load(SourceContent("http://public.example/data.csv"))

    assert "alpha" in result.content


def test_csv_loader_reads_public_url_through_redirect(web):
    web.redirect("http://public.example/data.csv", "http://cdn.example/data.csv")
    web.route(
        "http://cdn.example/data.csv",
        headers={"Content-Type": "text/csv"},
        body="name,value\ngamma,3\n",
    )

    result = CSVLoader().load(SourceContent("http://public.example/data.csv"))

    assert "gamma" in result.content


def test_same_origin_redirect_preserves_credentials(web, monkeypatch):
    monkeypatch.setenv("SESSION_VALUE", "COOKIE-SECRET")
    web.redirect("http://public.example/start", "/final")
    web.route(
        "http://public.example/final",
        headers=HTML,
        body="<html><body>Same Origin</body></html>",
    )
    tool = ScrapeWebsiteTool(
        website_url="http://public.example/start",
        cookies={"name": "session", "value": "SESSION_VALUE"},
    )
    tool.headers = {
        "User-Agent": "crew-test",
        "Authorization": "Bearer BEARER-SECRET",
        "X-Api-Key": "API-KEY-SECRET",
    }

    result = tool._run()

    assert "Same Origin" in result
    same_origin_calls = web.calls_to("public.example")
    assert len(same_origin_calls) == 2
    forwarded = same_origin_calls[1].header_text()
    assert "BEARER-SECRET" in forwarded
    assert "API-KEY-SECRET" in forwarded
    assert "COOKIE-SECRET" in forwarded


def test_unsafe_paths_opt_out_still_allows_internal_redirect(web, monkeypatch):
    monkeypatch.setenv("CREWAI_TOOLS_ALLOW_UNSAFE_PATHS", "true")
    web.redirect("http://public.example/start", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body>Internal Allowed</body></html>",
    )

    result = ScrapeWebsiteTool(website_url="http://public.example/start")._run()

    assert "Internal Allowed" in result
