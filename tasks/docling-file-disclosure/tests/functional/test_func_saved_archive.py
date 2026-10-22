# SPDX-License-Identifier: MIT
"""Saving and reloading a conversion archive keeps embedded and remote images."""

from conftest import document_dict, embedded_pixels
from docling_core.types.doc import DoclingDocument, ImageRefMode

from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.document import ConversionAssets


def test_archive_round_trip_keeps_images(tmp_path, images):
    _, uri_a, px_a = images["a"]
    _, uri_b, px_b = images["b"]
    remote = "https://example.com/figures/chart.png"
    doc = DoclingDocument.model_validate(document_dict(pictures=[uri_a, remote], page_uri=uri_b, table=True))
    archive = tmp_path / "saved" / "conversion.zip"
    ConversionAssets(status=ConversionStatus.SUCCESS, document=doc).save(filename=archive)

    loaded = ConversionAssets.load(filename=archive)

    assert loaded.status == ConversionStatus.SUCCESS
    assert loaded.document.export_to_dict() == doc.export_to_dict()
    assert str(loaded.document.pictures[1].image.uri) == remote
    md = loaded.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
    assert px_a in embedded_pixels(md)
    assert loaded.document.pages[1].image.pil_image.convert("RGB").tobytes() == px_b
