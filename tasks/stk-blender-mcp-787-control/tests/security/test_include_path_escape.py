"""Attached files of a Poly Haven model must stay inside the download's own folder."""

from support.fake_requests import FakeResponse
from support.harness import outside

MODEL_URL = "https://cdn.example/polyhaven/model.gltf"


def _serve_model(product, include):
    files = {
        "gltf": {
            "1k": {
                "gltf": {
                    "url": MODEL_URL,
                    "include": include,
                }
            }
        }
    }
    product.fake.add(
        lambda url: url.startswith("https://api.polyhaven.com/files/"),
        FakeResponse(json_data=files),
    )
    product.fake.add(MODEL_URL, FakeResponse(content=b"gltf-bytes"))
    for url in {info["url"] for info in include.values()}:
        product.fake.add(url, FakeResponse(content=b"attached-bytes"))


def _download(product):
    return product.call(
        "download_polyhaven_asset",
        {
            "asset_id": "probe-model",
            "asset_type": "models",
            "resolution": "1k",
            "file_format": "gltf",
        },
    )


def test_relative_traversal_attachment_writes_nothing_outside(product):
    destination = outside(product.root, "escape-relative")
    target = destination / "attachment.txt"
    assert not target.exists()

    _serve_model(
        product,
        {"../../escape-relative/attachment.txt": {"url": "https://cdn.example/rel"}},
    )
    _download(product)

    assert not target.exists(), "an attached file was written outside the download folder"


def test_absolute_attachment_path_writes_nothing_outside(product):
    destination = outside(product.root, "escape-absolute")
    target = destination / "attachment.txt"
    assert not target.exists()

    _serve_model(product, {str(target): {"url": "https://cdn.example/abs"}})
    _download(product)

    assert not target.exists(), "an attached file was written outside the download folder"


def test_traversal_attachment_creates_no_directory_outside(product):
    destination = outside(product.root, "escape-side-effect")
    new_directory = destination / "new-directory"
    assert not new_directory.exists()

    _serve_model(
        product,
        {
            "../../escape-side-effect/new-directory/attachment.txt": {
                "url": "https://cdn.example/side-effect"
            }
        },
    )
    _download(product)

    assert not new_directory.exists(), (
        "the download created a directory outside its own folder"
    )


def test_absolute_attachment_creates_no_directory_outside(product):
    destination = outside(product.root, "escape-absolute-side-effect")
    new_directory = destination / "new-directory"
    target = new_directory / "attachment.txt"
    assert not new_directory.exists()

    _serve_model(product, {str(target): {"url": "https://cdn.example/abs-side-effect"}})
    _download(product)

    assert not new_directory.exists(), (
        "the download created a directory outside its own folder"
    )
