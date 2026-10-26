"""Legitimate Poly Haven downloads keep writing every attached file where it belongs."""

from support.fake_requests import FakeResponse

MODEL_URL = "https://cdn.example/polyhaven/model.gltf"


def _serve(product, include=None):
    file_info = {"url": MODEL_URL}
    if include is not None:
        file_info["include"] = include
    files = {"gltf": {"1k": {"gltf": file_info}}}
    product.fake.add(
        lambda url: url.startswith("https://api.polyhaven.com/files/"),
        FakeResponse(json_data=files),
    )
    product.fake.add(MODEL_URL, FakeResponse(content=b"gltf-bytes"))
    for info in (include or {}).values():
        product.fake.add(info["url"], FakeResponse(content=b"attached-bytes"))


def _download(product):
    return product.call(
        "download_polyhaven_asset",
        {
            "asset_id": "legitimate-model",
            "asset_type": "models",
            "resolution": "1k",
            "file_format": "gltf",
        },
    )


def test_plain_model_still_downloads_and_imports(product):
    _serve(product)
    seen = product.snapshot_import()

    response = _download(product)

    assert response["result"]["success"] is True
    assert seen.get("filepath", "").endswith("model.gltf")
    assert "model.gltf" in seen.get("tree", [])


def test_nested_attachments_keep_their_relative_layout(product):
    include = {
        "textures/wood.png": {"url": "https://cdn.example/polyhaven/wood"},
        "materials/sub/sidecar.mtl": {"url": "https://cdn.example/polyhaven/sidecar"},
    }
    _serve(product, include)
    seen = product.snapshot_import()

    response = _download(product)

    assert response["result"]["success"] is True
    tree = seen.get("tree", [])
    assert "model.gltf" in tree
    assert "textures/wood.png" in tree, "a nested attached file lost its relative path"
    assert "materials/sub/sidecar.mtl" in tree, "a nested attached file lost its relative path"
