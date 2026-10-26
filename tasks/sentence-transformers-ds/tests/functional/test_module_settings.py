from __future__ import annotations

import numpy as np
import torch

from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.modules import CNN, Pooling, WordEmbeddings
from sentence_transformers.sentence_transformer.modules.tokenizer import WhitespaceTokenizer


def _word_embeddings() -> WordEmbeddings:
    vocab = ["alpha", "beta", "gamma"]
    weights = np.arange(len(vocab) * 4, dtype=np.float32).reshape(len(vocab), 4) + 1.0
    return WordEmbeddings(tokenizer=WhitespaceTokenizer(vocab=vocab), embedding_weights=weights)


def test_saved_cnn_with_a_builtin_activation_reloads(tmp_path):
    """A saved model that uses the library's own modules with a built-in activation keeps
    loading and producing the same embeddings."""
    cnn = CNN(in_embedding_dimension=4, out_channels=2, kernel_sizes=[1], activation_function=torch.nn.Tanh())
    model = SentenceTransformer(modules=[_word_embeddings(), cnn, Pooling(cnn.get_embedding_dimension())])
    expected = model.encode(["alpha beta", "gamma"], convert_to_numpy=True)

    path = tmp_path / "cnn-model"
    model.save_pretrained(str(path))
    loaded = SentenceTransformer(str(path), local_files_only=True)
    actual = loaded.encode(["alpha beta", "gamma"], convert_to_numpy=True)

    assert type(loaded[1]) is CNN
    assert np.allclose(expected, actual, atol=1e-6)


def test_saved_transformer_model_reloads_offline(tmp_path):
    """An ordinary saved model with a backbone module keeps reloading and embedding the same."""
    model = SentenceTransformer(
        "sentence-transformers-testing/stsb-bert-tiny-safetensors", local_files_only=True
    )
    expected = model.encode(["hello world"], convert_to_numpy=True)

    path = tmp_path / "transformer-model"
    model.save_pretrained(str(path))
    loaded = SentenceTransformer(str(path), local_files_only=True)
    actual = loaded.encode(["hello world"], convert_to_numpy=True)

    assert np.allclose(expected, actual, atol=1e-5)
