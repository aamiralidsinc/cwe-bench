# SPDX-License-Identifier: MIT
"""Documents returned by a conversion service keep their embedded and remote images."""

from conftest import document_dict, embedded_pixels
from docling_core.types.doc import DoclingDocument, ImageRefMode

import tests.fakes.docling_serve as fake_serve
from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.service.targets import InBodyTarget
from docling.service_client import DoclingServiceClient
from docling.service_client.client import StatusWatcherKind
from tests.fakes.docling_serve import FakeDoclingServe
from tests.fakes.http_service import FakeService


def test_service_document_keeps_images(images, monkeypatch):
    _, uri_a, px_a = images["a"]
    _, uri_b, px_b = images["b"]
    remote = "https://example.com/figures/chart.png"
    data = document_dict(pictures=[uri_a, remote], page_uri=uri_b, table=True)
    monkeypatch.setattr(fake_serve, "_fake_document",
                        lambda name: DoclingDocument.model_validate({**data, "name": name}))
    service = FakeService()
    serve = FakeDoclingServe()
    service.include(serve.router)
    service.start()
    serve.base_url = service.base_url
    serve.service = service
    try:
        with DoclingServiceClient(url=service.base_url, status_watcher=StatusWatcherKind.POLLING,
                                  poll_server_wait=0.01, poll_client_interval=0.01) as client:
            res = client.submit("https://example.com/report.pdf", target=InBodyTarget()).result()
    finally:
        service.stop()
    assert res.status == ConversionStatus.SUCCESS
    doc = res.document
    assert str(doc.pictures[1].image.uri) == remote
    md = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
    assert "Revenue" in md
    assert px_a in embedded_pixels(md)
    assert doc.pages[1].image.pil_image.convert("RGB").tobytes() == px_b
