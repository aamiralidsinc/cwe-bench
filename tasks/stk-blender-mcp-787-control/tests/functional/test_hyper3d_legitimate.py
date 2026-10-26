"""Legitimate generated-asset identifiers still import, on both Hyper3D transports."""

from support.fake_requests import FakeResponse

MAIN_SITE_URL = "https://hyperhuman.deemos.com/api/v2/download"
MODEL_URL = "https://cdn.example/hyper3d/model.glb"


def _serve_main_site(product):
    product.fake.add(
        MAIN_SITE_URL,
        FakeResponse(json_data={"list": [{"name": "model.glb", "url": MODEL_URL}]}),
    )
    product.fake.add(MODEL_URL, FakeResponse(content=b"glb-bytes"))


def _serve_fal_ai(product):
    product.fake.add(
        lambda url: url.startswith("https://queue.fal.run/fal-ai/hyper3d/requests/"),
        FakeResponse(json_data={"model_mesh": {"url": MODEL_URL}}),
    )
    product.fake.add(MODEL_URL, FakeResponse(content=b"glb-bytes"))


def test_main_site_imports_with_a_legitimate_task_identifier(product):
    _serve_main_site(product)

    response = product.call(
        "import_generated_asset",
        {"name": "probe", "task_uuid": "task-1234-5678"},
    )

    assert response["result"]["succeed"] is True
    assert response["result"]["type"] == "MESH"
    assert list(product.private.rglob("*.glb")), "the import left no temporary model file"


def test_fal_ai_imports_with_a_legitimate_request_identifier(product):
    product.bpy.context.scene.blendermcp_hyper3d_mode = "FAL_AI"
    _serve_fal_ai(product)

    response = product.call(
        "import_generated_asset",
        {"name": "probe", "request_id": "req-1234-5678"},
    )

    assert response["result"]["succeed"] is True
    assert response["result"]["type"] == "MESH"
    assert list(product.private.rglob("*.glb")), "the import left no temporary model file"
