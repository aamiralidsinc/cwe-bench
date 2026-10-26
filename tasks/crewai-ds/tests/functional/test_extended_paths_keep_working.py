"""Legitimate use of the remaining remote-read paths keeps working."""

from __future__ import annotations

from io import BytesIO
import json

from crewai_tools.rag.loaders.docs_site_loader import DocsSiteLoader
from crewai_tools.rag.loaders.docx_loader import DOCXLoader
from crewai_tools.rag.loaders.pdf_loader import PDFLoader
from crewai_tools.rag.source_content import SourceContent
from crewai_tools.tools.jina_scrape_website_tool.jina_scrape_website_tool import (
    JinaScrapeWebsiteTool,
)
from crewai_tools.tools.serply_api_tool.serply_news_search_tool import (
    SerplyNewsSearchTool,
)

HTML = {"Content-Type": "text/html"}


def _pdf_bytes(text: str = "HELLO PDF") -> bytes:
    import pymupdf

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def _docx_bytes(text: str = "HELLO DOCX") -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_docs_loader_reads_navigation_pages(web):
    page = (
        "<html><head><title>Guide</title></head><body>"
        '<nav><a href="/intro">Intro</a></nav>'
        "<main><h1>Guide</h1><p>Body text</p></main></body></html>"
    )
    web.route("http://docs.example/guide", headers=HTML, body=page)
    web.route(
        "http://docs.example/intro",
        headers=HTML,
        body="<html><head><title>Intro</title></head><body><h1>Getting Started</h1></body></html>",
    )

    result = DocsSiteLoader().load(SourceContent("http://docs.example/guide"))

    assert "Getting Started" in result.content


def test_pdf_loader_downloads_public_pdf(web):
    web.route(
        "http://public.example/doc.pdf",
        headers={"Content-Type": "application/pdf"},
        body=_pdf_bytes("HELLO PDF"),
    )

    result = PDFLoader().load(SourceContent("http://public.example/doc.pdf"))

    assert "HELLO PDF" in result.content


def test_pdf_loader_follows_public_redirect(web):
    web.redirect("http://public.example/doc.pdf", "http://cdn.example/doc.pdf")
    web.route(
        "http://cdn.example/doc.pdf",
        headers={"Content-Type": "application/pdf"},
        body=_pdf_bytes("REDIRECTED PDF"),
    )

    result = PDFLoader().load(SourceContent("http://public.example/doc.pdf"))

    assert "REDIRECTED PDF" in result.content


def test_docx_loader_downloads_public_docx(web):
    web.route(
        "http://public.example/doc.docx",
        headers={"Content-Type": "application/octet-stream"},
        body=_docx_bytes("HELLO DOCX"),
    )

    result = DOCXLoader().load(SourceContent("http://public.example/doc.docx"))

    assert "HELLO DOCX" in result.content


def test_jina_tool_returns_reader_content(web):
    web.route(
        "https://r.jina.ai/http://public.example/start",
        headers={"Content-Type": "text/plain"},
        body="Reader Markdown",
    )

    result = JinaScrapeWebsiteTool(
        website_url="http://public.example/start"
    )._run()

    assert "Reader Markdown" in result


def test_jina_tool_falls_back_to_public_page(web):
    web.route(
        "https://r.jina.ai/http://public.example/start",
        status=503,
        headers={"Content-Type": "text/plain"},
        body="reader unavailable",
    )
    web.redirect("http://public.example/start", "http://public.example/final")
    web.route(
        "http://public.example/final",
        headers=HTML,
        body="<html><body>Fallback Content</body></html>",
    )

    result = JinaScrapeWebsiteTool(
        website_url="http://public.example/start"
    )._run()

    assert "Fallback Content" in result


def test_news_search_reports_final_public_link(web, monkeypatch):
    monkeypatch.setenv("SERPLY_API_KEY", "test-key")
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
    web.route(
        "https://api.serply.io/v1/news/q=example",
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload),
    )
    web.redirect("http://news.example/item", "http://news.example/final")
    web.route(
        "http://news.example/final",
        headers=HTML,
        body="<html><body>Article</body></html>",
    )

    result = SerplyNewsSearchTool()._run(search_query="example")

    assert "Link: http://news.example/final" in result
