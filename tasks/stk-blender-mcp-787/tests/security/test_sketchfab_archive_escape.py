"""A Sketchfab download must choose its own archive location, not follow the identifier."""

from support.fake_requests import FakeResponse
from support.harness import make_zip, outside

ARCHIVE_URL = "https://cdn.example/sketchfab/model.zip"


def _serve_archive(product):
    product.fake.add(
        lambda url: url.startswith("https://api.sketchfab.com/v3/models/"),
        FakeResponse(json_data={"gltf": {"url": ARCHIVE_URL}}),
    )
    product.fake.add(
        ARCHIVE_URL,
        FakeResponse(content=make_zip({"scene.gltf": b"{}"})),
    )


def _download(product, uid):
    return product.call("download_sketchfab_model", {"uid": uid, "target_size": 1.0})


def test_relative_identifier_cannot_move_the_archive(product):
    destination = outside(product.root, "archive-relative")
    assert not list(destination.iterdir())

    _serve_archive(product)
    _download(product, "../../archive-relative/payload")

    assert not list(destination.iterdir()), (
        "the download wrote its archive outside its own temporary folder"
    )


def test_absolute_identifier_cannot_move_the_archive(product):
    destination = outside(product.root, "archive-absolute")
    assert not list(destination.iterdir())

    _serve_archive(product)
    _download(product, str(destination / "payload"))

    assert not list(destination.iterdir()), (
        "the download wrote its archive outside its own temporary folder"
    )
