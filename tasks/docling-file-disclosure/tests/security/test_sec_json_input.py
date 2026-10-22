# SPDX-License-Identifier: MIT
"""Converting a Docling JSON file must not disclose local files it names as images."""

import json
from pathlib import Path

from conftest import assert_not_disclosed, document_dict, loaded_or_none
from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter


def _convert(json_file: Path):
    def run():
        res = DocumentConverter().convert(json_file, raises_on_error=False)
        if res.status not in (ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS):
            return None
        return res.document
    return loaded_or_none(run)


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "inbox" / "report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_json_picture_absolute_path(tmp_path, private_image):
    path, pixels = private_image
    doc = _convert(_write(tmp_path, document_dict(picture_uri=str(path))))
    assert_not_disclosed(doc, tmp_path / "out", pixels)


def test_json_picture_relative_path(tmp_path, private_image, monkeypatch):
    path, pixels = private_image
    monkeypatch.chdir(path.parent.parent)
    rel = f"{path.parent.name}/{path.name}"
    doc = _convert(_write(tmp_path, document_dict(picture_uri=rel)))
    assert_not_disclosed(doc, tmp_path / "out", pixels)


def test_json_picture_file_uri(tmp_path, private_image):
    path, pixels = private_image
    doc = _convert(_write(tmp_path, document_dict(picture_uri=path.as_uri())))
    assert_not_disclosed(doc, tmp_path / "out", pixels)


def test_json_page_image_path(tmp_path, private_image):
    path, pixels = private_image
    doc = _convert(_write(tmp_path, document_dict(page_uri=str(path))))
    assert_not_disclosed(doc, tmp_path / "out", pixels)
