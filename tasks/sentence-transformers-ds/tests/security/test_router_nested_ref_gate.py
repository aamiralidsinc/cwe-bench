from __future__ import annotations

import json

from sentence_transformers import SentenceTransformer

from support import MODULE_CLASS, install_probe, run_capture, write_model_dir


def test_untrusted_route_type_in_a_saved_router(tmp_path, monkeypatch):
    """A routing module keeps its own route configuration. A class named there must not be
    imported without an explicit opt-in, just like a top-level module class."""
    marker = install_probe(tmp_path, monkeypatch, "probe_router", MODULE_CLASS)

    model_dir = tmp_path / "model"
    write_model_dir(
        model_dir,
        [
            {
                "idx": 0,
                "name": "0",
                "path": "0_Router",
                "type": "sentence_transformers.base.modules.router.Router",
            }
        ],
    )
    router_dir = model_dir / "0_Router"
    router_dir.mkdir()
    (router_dir / "router_config.json").write_text(
        json.dumps(
            {
                "types": {"route_a": "probe_router.MarkerModule"},
                "structure": {"sentence_embedding": ["route_a"]},
                "parameters": {"default_route": None, "allow_empty_key": True, "route_mappings": {}},
            }
        )
    )

    _, exc = run_capture(lambda: SentenceTransformer(str(model_dir), local_files_only=True))

    assert not marker.exists(), "the route class named by the saved model was imported"
    assert exc is not None, "the load was expected to refuse"
