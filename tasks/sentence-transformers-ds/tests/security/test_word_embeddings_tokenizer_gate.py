from __future__ import annotations

import json

import numpy as np

from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.modules import WordEmbeddings
from sentence_transformers.sentence_transformer.modules.tokenizer import WhitespaceTokenizer

from support import TOKENIZER_CLASS, install_probe, run_capture, write_model_dir


def test_untrusted_tokenizer_class_in_a_saved_embedding_model(tmp_path, monkeypatch):
    """A saved embedding model carries the tokenizer's class in its own configuration. Loading
    that model must not import a class outside the library without an explicit opt-in."""
    marker = install_probe(tmp_path, monkeypatch, "probe_word_embeddings", TOKENIZER_CLASS)

    module_dir = tmp_path / "model" / "0_WordEmbeddings"
    module_dir.mkdir(parents=True)
    module = WordEmbeddings(
        tokenizer=WhitespaceTokenizer(vocab=["alpha", "beta"]),
        embedding_weights=np.zeros((2, 4), dtype=np.float32),
    )
    module.save(str(module_dir))

    config_path = module_dir / "wordembedding_config.json"
    config = json.loads(config_path.read_text())
    config["tokenizer_class"] = "probe_word_embeddings.MarkerTokenizer"
    config_path.write_text(json.dumps(config))

    write_model_dir(
        tmp_path / "model",
        [
            {
                "idx": 0,
                "name": "0",
                "path": "0_WordEmbeddings",
                "type": f"{type(module).__module__}.{type(module).__name__}",
            }
        ],
    )

    _, exc = run_capture(lambda: SentenceTransformer(str(tmp_path / "model"), local_files_only=True))

    assert not marker.exists(), "the tokenizer class named by the saved model was imported"
    assert exc is not None, "the load was expected to refuse"
