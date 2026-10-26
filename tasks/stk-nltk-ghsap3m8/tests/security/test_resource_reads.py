"""A resource name resolved against the configured data locations must not reach a
file outside them, and a file id joined onto a corpus root must not leave that root."""
from urllib.parse import quote

import pytest

import nltk.data


def _data_tree(tmp_path):
    base = tmp_path / "base"
    data = base / "data"
    (data / "corpora" / "sub").mkdir(parents=True)
    (base / "secret.txt").write_text("SECRET-OUTSIDE")
    (data / "corpora" / "top.txt").write_text("TOP")
    (data / "corpora" / "sub" / "nested.txt").write_text("NESTED")
    nltk.data.path[:] = [str(data)]
    return base, data


def _corpus_reader(data):
    from nltk.corpus.reader.plaintext import PlaintextCorpusReader

    return PlaintextCorpusReader(str(data / "corpora"), r".*")


def test_literal_parent_segment_is_refused(tmp_path):
    _data_tree(tmp_path)
    with pytest.raises(Exception):
        nltk.data.load("nltk:../secret.txt", format="text")


def test_percent_encoded_parent_segment_is_refused(tmp_path):
    _data_tree(tmp_path)
    with pytest.raises(Exception):
        nltk.data.load("nltk:%2e%2e/secret.txt", format="text")


def test_mixed_encoded_parent_segments_are_refused(tmp_path):
    _data_tree(tmp_path)
    with pytest.raises(Exception):
        nltk.data.load("nltk:corpora/%2e%2e/%2e%2e/secret.txt", format="text")


def test_encoded_absolute_path_is_refused(tmp_path):
    base, _data = _data_tree(tmp_path)
    encoded = quote((base / "secret.txt").as_posix(), safe="")
    with pytest.raises(Exception):
        nltk.data.load("nltk:" + encoded, format="text")


def test_corpus_file_id_does_not_escape_root(tmp_path):
    base, data = _data_tree(tmp_path)
    reader = _corpus_reader(data)
    with pytest.raises(Exception):
        reader.open("../../secret.txt").read()


def test_corpus_absolute_file_id_does_not_escape_root(tmp_path):
    base, data = _data_tree(tmp_path)
    reader = _corpus_reader(data)
    with pytest.raises(Exception):
        reader.open(str(base / "secret.txt")).read()
