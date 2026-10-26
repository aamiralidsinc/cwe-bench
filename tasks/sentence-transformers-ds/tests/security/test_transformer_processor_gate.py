from __future__ import annotations

import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.base.modules import Transformer

from support import PROCESSOR_CLASS, install_probe, run_capture, write_model_dir


def test_untrusted_processor_class_in_a_saved_transformer_module(tmp_path, monkeypatch):
    """A backbone module's saved settings can name a processor class. Loading the model must not
    import a class outside the library without an explicit opt-in."""
    marker = install_probe(tmp_path, monkeypatch, "probe_processor", PROCESSOR_CLASS)

    model_dir = tmp_path / "model"
    module_dir = model_dir / "0_Transformer"
    module_dir.mkdir(parents=True)
    (module_dir / "sentence_bert_config.json").write_text(
        json.dumps(
            {
                "processor_class": "probe_processor.MarkerProcessor",
                "max_seq_length": 32,
                "do_lower_case": False,
            }
        )
    )

    write_model_dir(
        model_dir,
        [
            {
                "idx": 0,
                "name": "0",
                "path": "0_Transformer",
                "type": f"{Transformer.__module__}.{Transformer.__name__}",
            }
        ],
    )

    run_capture(lambda: SentenceTransformer(str(model_dir), local_files_only=True))

    assert not marker.exists(), "the processor class named by the saved settings was imported"
