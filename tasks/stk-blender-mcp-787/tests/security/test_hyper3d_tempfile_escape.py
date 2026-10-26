"""A generated-asset import must choose its own temporary file, not follow the identifier."""

from support.fake_requests import FakeResponse
from support.harness import outside

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


def test_absolute_task_identifier_cannot_choose_the_temporary_location(product):
    destination = outside(product.root, "hyper3d-absolute")
    assert not list(destination.iterdir())

    _serve_main_site(product)
    product.call(
        "import_generated_asset",
        {"name": "probe", "task_uuid": str(destination / "payload")},
    )

    assert not list(destination.iterdir()), (
        "the import created its temporary file outside the temporary location"
    )


def test_relative_task_identifier_cannot_choose_the_temporary_location(product):
    destination = outside(product.root, "hyper3d-relative")
    assert not list(destination.iterdir())

    _serve_main_site(product)
    product.call(
        "import_generated_asset",
        {"name": "probe", "task_uuid": "../hyper3d-relative/payload"},
    )

    assert not list(destination.iterdir()), (
        "the import created its temporary file outside the temporary location"
    )


def test_absolute_request_identifier_cannot_choose_the_temporary_location(product):
    destination = outside(product.root, "hyper3d-fal-absolute")
    assert not list(destination.iterdir())

    product.bpy.context.scene.blendermcp_hyper3d_mode = "FAL_AI"
    _serve_fal_ai(product)
    product.call(
        "import_generated_asset",
        {"name": "probe", "request_id": str(destination / "payload")},
    )

    assert not list(destination.iterdir()), (
        "the import created its temporary file outside the temporary location"
    )
