"""The reported scraping entry points must not reach internal destinations."""

from __future__ import annotations

import pytest

from crewai_tools.tools.scrape_element_from_website.scrape_element_from_website import (
    ScrapeElementFromWebsiteTool,
)
from crewai_tools.tools.scrape_website_tool.scrape_website_tool import (
    ScrapeWebsiteTool,
)

HTML = {"Content-Type": "text/html"}


def _scrape(url: str) -> object:
    return ScrapeWebsiteTool(website_url=url)._run()


def _scrape_element(url: str) -> object:
    tool = ScrapeElementFromWebsiteTool(website_url=url, css_element="body")
    return tool._run()


def test_web_page_scraper_does_not_follow_redirect_to_internal_host(web):
    web.redirect("http://public.example/start", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body>INTERNAL-MARKER</body></html>",
    )

    with pytest.raises(Exception):
        _scrape("http://public.example/start")

    assert web.calls_to("internal.example") == []


def test_web_page_scraper_does_not_follow_scheme_relative_redirect_to_internal_host(web):
    web.redirect("http://public.example/start", "//internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body>INTERNAL-MARKER</body></html>",
    )

    with pytest.raises(Exception):
        _scrape("http://public.example/start")

    assert web.calls_to("internal.example") == []


def test_web_page_scraper_does_not_follow_redirect_to_link_local_address(web):
    web.redirect(
        "http://public.example/start",
        "http://169.254.169.254/latest/meta-data/",
    )
    web.route(
        "http://169.254.169.254/latest/meta-data/",
        headers={"Content-Type": "text/plain"},
        body="INSTANCE-CREDENTIALS",
    )

    with pytest.raises(Exception):
        _scrape("http://public.example/start")

    assert web.calls_to("169.254.169.254") == []


def test_web_page_scraper_does_not_follow_multi_hop_redirect_to_internal_host(web):
    web.redirect("http://public.example/start", "http://cdn.example/hop")
    web.redirect("http://cdn.example/hop", "http://vault.example/secret")
    web.route(
        "http://vault.example/secret",
        headers=HTML,
        body="<html><body>INTERNAL-MARKER</body></html>",
    )

    with pytest.raises(Exception):
        _scrape("http://public.example/start")

    assert web.calls_to("vault.example") == []


def test_element_scraper_does_not_follow_redirect_to_internal_host(web):
    web.redirect("http://public.example/start", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body='<html><body><div class="secret">INTERNAL-MARKER</div></body></html>',
    )

    with pytest.raises(Exception):
        _scrape_element("http://public.example/start")

    assert web.calls_to("internal.example") == []
