# SPDX-License-Identifier: MIT
"""Loading a saved conversion archive must not disclose local files it names as images."""

import json
import zipfile

from conftest import assert_not_disclosed, document_dict, loaded_or_none
from docling.datamodel.document import ConversionAssets


def test_archive_document_images(tmp_path, private_image, monkeypatch):
    path, pixels = private_image
    monkeypatch.chdir(path.parent.parent)
    data = document_dict(picture_uri=str(path), page_uri=f"{path.parent.name}/{path.name}")
    archive = tmp_path / "shared" / "conversion.zip"
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("status.json", json.dumps("success"))
        zf.writestr("document.json", json.dumps(data))

    loaded = loaded_or_none(lambda: ConversionAssets.load(filename=archive))
    assert_not_disclosed(None if loaded is None else loaded.document, tmp_path / "out", pixels)
