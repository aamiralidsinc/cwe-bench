"""Legitimate resource loads keep working: nested names inside the configured data
locations, explicit absolute file URLs, corpus file ids and retrieval."""
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


def test_nested_resource_name_loads(tmp_path):
    _data_tree(tmp_path)
    assert nltk.data.load("nltk:corpora/sub/nested.txt", format="text") == "NESTED"


def test_relative_parent_segments_inside_a_data_location_resolve(tmp_path):
    _data_tree(tmp_path)
    assert nltk.data.load("nltk:corpora/sub/../top.txt", format="text") == "TOP"


def test_absolute_file_url_loads(tmp_path):
    base, _data = _data_tree(tmp_path)
    url = "file://" + (base / "secret.txt").as_posix()
    assert nltk.data.load(url, format="text") == "SECRET-OUTSIDE"


def test_corpus_reader_reads_nested_file_id(tmp_path):
    _data, data = _data_tree(tmp_path)
    from nltk.corpus.reader.plaintext import PlaintextCorpusReader

    reader = PlaintextCorpusReader(str(data / "corpora"), r".*")
    assert reader.open("sub/nested.txt").read() == "NESTED"


def test_retrieve_writes_a_relative_output_file(tmp_path, monkeypatch):
    _data_tree(tmp_path)
    workdir = tmp_path / "work"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    nltk.data.retrieve("nltk:corpora/top.txt", "copy.txt", verbose=False)
    assert (workdir / "copy.txt").read_text() == "TOP"
