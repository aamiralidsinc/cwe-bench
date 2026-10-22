# SPDX-License-Identifier: MIT
"""A document returned by a conversion service must not disclose local files it names as images."""

from conftest import assert_not_disclosed, document_dict, loaded_or_none
from docling_core.types.doc import DoclingDocument

import tests.fakes.docling_serve as fake_serve
from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.service.targets import InBodyTarget
from docling.service_client import DoclingServiceClient
from docling.service_client.client import StatusWatcherKind
from tests.fakes.docling_serve import FakeDoclingServe
from tests.fakes.http_service import FakeService


def test_service_document_images(tmp_path, private_image, monkeypatch):
    path, pixels = private_image
    monkeypatch.chdir(path.parent.parent)
    data = document_dict(picture_uri=str(path), page_uri=f"{path.parent.name}/{path.name}")
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
            def run():
                res = client.submit("https://example.com/report.pdf", target=InBodyTarget()).result()
                if res.status not in (ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS):
                    return None
                return res.document
            doc = loaded_or_none(run)
    finally:
        service.stop()
    assert_not_disclosed(doc, tmp_path / "out", pixels)
