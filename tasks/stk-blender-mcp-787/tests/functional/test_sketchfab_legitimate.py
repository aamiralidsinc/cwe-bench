"""A legitimate Sketchfab identifier still downloads, extracts and imports the model."""

from support.fake_requests import FakeResponse
from support.harness import make_zip

ARCHIVE_URL = "https://cdn.example/sketchfab/model.zip"


def test_legitimate_identifier_downloads_and_imports(product):
    product.fake.add(
        lambda url: url.startswith("https://api.sketchfab.com/v3/models/"),
        FakeResponse(json_data={"gltf": {"url": ARCHIVE_URL}}),
    )
    product.fake.add(
        ARCHIVE_URL,
        FakeResponse(
            content=make_zip(
                {
                    "scene.gltf": b"{}",
                    "textures/albedo.png": b"image-bytes",
                }
            )
        ),
    )
    seen = product.snapshot_import()

    response = product.call(
        "download_sketchfab_model",
        {"uid": "a1b2c3d4e5f6", "target_size": 1.0},
    )

    result = response["result"]
    assert result["success"] is True
    assert result["imported_objects"], "the imported model has no objects"
    assert seen.get("filepath", "").endswith("scene.gltf")
