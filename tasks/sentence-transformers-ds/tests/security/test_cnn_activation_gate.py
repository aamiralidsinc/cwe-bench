from __future__ import annotations

import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.modules import CNN

from support import ACTIVATION_CLASS, install_probe, run_capture, write_model_dir


def test_untrusted_activation_class_in_a_saved_cnn_module(tmp_path, monkeypatch):
    """A saved module can name a callable in its own configuration. Loading the model must not
    import a callable outside the library without an explicit opt-in."""
    marker = install_probe(tmp_path, monkeypatch, "probe_cnn_activation", ACTIVATION_CLASS)

    model_dir = tmp_path / "model"
    module_dir = model_dir / "0_CNN"
    module_dir.mkdir(parents=True)
    module = CNN(in_embedding_dimension=8)
    module.save(str(module_dir))

    config_path = module_dir / "cnn_config.json"
    config = json.loads(config_path.read_text())
    config["activation_function"] = "probe_cnn_activation.MarkerActivation"
    config_path.write_text(json.dumps(config))

    write_model_dir(
        model_dir,
        [
            {
                "idx": 0,
                "name": "0",
                "path": "0_CNN",
                "type": f"{type(module).__module__}.{type(module).__name__}",
            }
        ],
    )

    run_capture(lambda: SentenceTransformer(str(model_dir), local_files_only=True))

    assert not marker.exists(), "the callable named by the saved module was imported"
