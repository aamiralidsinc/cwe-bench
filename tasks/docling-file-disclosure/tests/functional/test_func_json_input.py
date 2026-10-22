# SPDX-License-Identifier: MIT
"""Legitimate Docling JSON input keeps converting exactly as before."""

import json
from io import BytesIO
from pathlib import Path

from conftest import document_dict, embedded_pixels
from docling_core.types.doc import ImageRefMode

from docling.datamodel.base_models import ConversionStatus, DocumentStream
from docling.document_converter import DocumentConverter


def _convert(tmp_path: Path, data: dict):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    res = DocumentConverter().convert(path)
    assert res.status == ConversionStatus.SUCCESS
    return res.document


def test_embedded_picture_is_kept(tmp_path, images):
    _, uri, pixels = images["a"]
    doc = _convert(tmp_path, document_dict(pictures=[uri]))
    assert doc.pictures[0].image is not None
    assert str(doc.pictures[0].image.uri) == uri
    assert pixels in embedded_pixels(doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED))


def test_remote_picture_link_is_kept(tmp_path):
    remote = "https://example.com/figures/chart.png"
    doc = _convert(tmp_path, document_dict(pictures=[remote]))
    assert doc.pictures[0].image is not None
    assert str(doc.pictures[0].image.uri) == remote


def test_embedded_page_image_is_kept(tmp_path, images):
    _, uri, pixels = images["b"]
    doc = _convert(tmp_path, document_dict(page_uri=uri))
    assert doc.pages[1].image is not None
    assert str(doc.pages[1].image.uri) == uri
    assert doc.pages[1].image.pil_image.convert("RGB").tobytes() == pixels


def test_document_content_survives_alongside_images(tmp_path, images):
    _, uri_a, px_a = images["a"]
    _, uri_b, px_b = images["b"]
    data = document_dict(pictures=[uri_a, "https://example.com/x.png", uri_b], table=True)
    doc = _convert(tmp_path, data)
    md = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
    assert "Quarterly report body text." in md
    assert "Revenue" in md and "4711" in md
    found = embedded_pixels(md)
    assert px_a in found and px_b in found
    assert len(doc.pictures) == 3


def test_stream_input_round_trips(images):
    _, uri, _ = images["a"]
    data = document_dict(pictures=[uri, "http://example.org/a.png"], table=True)
    stream = DocumentStream(name="report.json", stream=BytesIO(json.dumps(data).encode()))
    res = DocumentConverter().convert(stream)
    assert res.status == ConversionStatus.SUCCESS
    assert res.document.export_to_dict() == data
