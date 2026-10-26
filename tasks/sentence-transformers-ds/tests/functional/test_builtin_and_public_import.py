from __future__ import annotations

import json
from collections import OrderedDict

import numpy as np

from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.modules import Pooling, WordEmbeddings
from sentence_transformers.sentence_transformer.modules.tokenizer import WhitespaceTokenizer
from sentence_transformers.util import import_module_class


def _word_embeddings() -> WordEmbeddings:
    vocab = ["alpha", "beta", "gamma"]
    weights = np.arange(len(vocab) * 4, dtype=np.float32).reshape(len(vocab), 4) + 1.0
    return WordEmbeddings(tokenizer=WhitespaceTokenizer(vocab=vocab), embedding_weights=weights)


def test_saved_model_with_builtin_classes_reloads_without_opt_in(tmp_path):
    """A model built from the library's own modules saves class references in the library's
    namespace; reloading it must keep working with no opt-in and produce the same embeddings."""
    model = SentenceTransformer(modules=[_word_embeddings(), Pooling(4)])
    expected = model.encode(["alpha beta", "gamma"], convert_to_numpy=True)

    path = tmp_path / "saved"
    model.save_pretrained(str(path))

    saved = json.loads((path / "modules.json").read_text())
    assert all(entry["type"].startswith("sentence_transformers.") for entry in saved)

    loaded = SentenceTransformer(str(path), local_files_only=True)
    actual = loaded.encode(["alpha beta", "gamma"], convert_to_numpy=True)
    assert np.allclose(expected, actual, atol=1e-6)


def test_public_import_helper_without_a_model_location():
    """The public helper still imports an installed class when no model is involved."""
    assert import_module_class("collections.OrderedDict") is OrderedDict
    assert import_module_class("collections.OrderedDict", model_name_or_path=None) is OrderedDict


def test_builtin_class_reference_with_a_model_location():
    """A built-in class reference is not affected by the model location."""
    cls = import_module_class(
        "sentence_transformers.sentence_transformer.modules.Pooling",
        model_name_or_path="example-org/some-model",
        trust_remote_code=False,
    )
    assert cls is Pooling
