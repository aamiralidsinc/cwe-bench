from __future__ import annotations

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from support import install_probe

CUSTOM_MODELING_FILE = '''
import os
from pathlib import Path

_marker = os.environ.get("CWE_MARKER_FILE")
if _marker:
    Path(_marker).write_text("imported")

import torch

from sentence_transformers.base.modules import InputModule


class CustomProbeModule(InputModule):
    def __init__(self, factor: float = 1.0):
        super().__init__()
        self.factor = factor
        self.embeddings_dimension = 4

    def preprocess(self, inputs, **kwargs):
        return {"input_ids": torch.zeros((len(inputs), 1), dtype=torch.long)}

    def forward(self, features, **kwargs):
        features["sentence_embedding"] = torch.zeros((1, self.embeddings_dimension))
        return features

    def get_embedding_dimension(self):
        return self.embeddings_dimension

    @classmethod
    def load(cls, model_name_or_path, subfolder="", **kwargs):
        return cls()

    def save(self, output_path, *args, **kwargs):
        pass
'''


def test_a_local_custom_module_loads_with_an_explicit_opt_in(tmp_path, monkeypatch):
    """The documented way to run a model's own modeling file keeps working: the caller's
    explicit opt-in loads the class and the model is usable."""
    marker = install_probe(tmp_path, monkeypatch, "custom_module_probe", CUSTOM_MODELING_FILE)

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "custom_module_probe.py").write_text(
        (tmp_path / "probes" / "custom_module_probe.py").read_text()
    )
    (model_dir / "modules.json").write_text(
        json.dumps(
            [
                {
                    "idx": 0,
                    "name": "0",
                    "path": "0_Model",
                    "type": "custom_module_probe.CustomProbeModule",
                }
            ]
        )
    )
    (model_dir / "config_sentence_transformers.json").write_text('{"model_type": "SentenceTransformer"}')
    (model_dir / "0_Model").mkdir()

    model = SentenceTransformer(str(model_dir), local_files_only=True, trust_remote_code=True)

    assert marker.exists(), "the explicitly trusted modeling file was not executed"
    assert type(model[0]).__name__ == "CustomProbeModule"
