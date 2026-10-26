"""Every supported content loader must refuse an internal redirect target."""

from __future__ import annotations

import pytest

from crewai_tools.rag.loaders.csv_loader import CSVLoader
from crewai_tools.rag.loaders.docs_site_loader import DocsSiteLoader
from crewai_tools.rag.loaders.docx_loader import DOCXLoader
from crewai_tools.rag.loaders.pdf_loader import PDFLoader
from crewai_tools.rag.loaders.webpage_loader import WebPageLoader
from crewai_tools.rag.source_content import SourceContent

HTML = {"Content-Type": "text/html"}


def test_web_page_loader_does_not_follow_redirect_to_internal_host(web):
    web.redirect("http://public.example/page", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body>INTERNAL-MARKER</body></html>",
    )

    with pytest.raises(Exception):
        WebPageLoader().load(SourceContent("http://public.example/page"))

    assert web.calls_to("internal.example") == []


def test_docs_site_loader_does_not_follow_redirect_to_internal_host(web):
    web.redirect("http://docs.example/guide", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers=HTML,
        body="<html><body><main>INTERNAL-MARKER</main></body></html>",
    )

    with pytest.raises(Exception):
        DocsSiteLoader().load(SourceContent("http://docs.example/guide"))

    assert web.calls_to("internal.example") == []


def test_pdf_loader_does_not_follow_redirect_to_internal_host(web):
    web.route(
        "http://public.example/doc.pdf",
        status=200,
        headers={"Content-Type": "application/pdf"},
        body=b"%PDF-1.4\nok\n%%EOF",
        method="HEAD",
    )
    web.redirect(
        "http://public.example/doc.pdf",
        "http://internal.example/admin",
        method="GET",
    )
    web.route(
        "http://internal.example/admin",
        headers={"Content-Type": "application/pdf"},
        body=b"%PDF-1.4\nINTERNAL-MARKER\n%%EOF",
    )

    with pytest.raises(Exception):
        PDFLoader().load(SourceContent("http://public.example/doc.pdf"))

    assert web.calls_to("internal.example") == []


def test_docx_loader_does_not_follow_redirect_to_internal_host(web):
    web.redirect("http://public.example/doc.docx", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers={"Content-Type": "application/octet-stream"},
        body=b"INTERNAL-MARKER",
    )

    with pytest.raises(Exception):
        DOCXLoader().load(SourceContent("http://public.example/doc.docx"))

    assert web.calls_to("internal.example") == []


def test_csv_loader_does_not_follow_redirect_to_internal_host(web):
    web.redirect("http://public.example/data.csv", "http://internal.example/admin")
    web.route(
        "http://internal.example/admin",
        headers={"Content-Type": "text/csv"},
        body="name,value\nINTERNAL,MARKER\n",
    )

    with pytest.raises(Exception):
        CSVLoader().load(SourceContent("http://public.example/data.csv"))

    assert web.calls_to("internal.example") == []
