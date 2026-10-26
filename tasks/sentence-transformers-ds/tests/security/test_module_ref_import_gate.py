from __future__ import annotations

from pathlib import Path

from sentence_transformers import CrossEncoder, SentenceTransformer
from sentence_transformers.util import import_module_class

from support import MODULE_CLASS, install_probe, run_capture, write_model_dir


def _saved_modules_dir(tmp_path: Path, module_name: str, subdir: str, model_type: str = "SentenceTransformer") -> Path:
    model_dir = tmp_path / "model"
    (model_dir / subdir).mkdir(parents=True, exist_ok=True)
    write_model_dir(
        model_dir,
        [{"idx": 0, "name": "0", "path": subdir, "type": f"{module_name}.MarkerModule"}],
        model_type=model_type,
    )
    return model_dir


def test_untrusted_module_class_in_local_model_directory(tmp_path, monkeypatch):
    """A saved model in a local directory names a class outside the library; loading it must not
    import that class when the caller did not allow untrusted code."""
    marker = install_probe(tmp_path, monkeypatch, "probe_local_model", MODULE_CLASS)
    model_dir = _saved_modules_dir(tmp_path, "probe_local_model", "0_probe")

    _, exc = run_capture(lambda: SentenceTransformer(str(model_dir), local_files_only=True))

    assert not marker.exists(), "the class named by the saved model was imported"
    assert exc is not None, "the load was expected to refuse"


def test_untrusted_module_class_for_a_hub_reference(tmp_path, monkeypatch):
    """Same reference, but the model is identified by a repository id rather than a local path."""
    marker = install_probe(tmp_path, monkeypatch, "probe_hub_ref", MODULE_CLASS)

    _, exc = run_capture(
        lambda: import_module_class(
            "probe_hub_ref.MarkerModule",
            model_name_or_path="example-org/untrusted-embeddings",
            trust_remote_code=False,
        )
    )

    assert not marker.exists(), "the class named by the repository configuration was imported"
    assert exc is not None, "the load was expected to refuse"


def test_untrusted_module_class_with_no_trust_decision(tmp_path, monkeypatch):
    """An absent trust decision is not an opt-in."""
    marker = install_probe(tmp_path, monkeypatch, "probe_none_trust", MODULE_CLASS)

    _, exc = run_capture(
        lambda: import_module_class(
            "probe_none_trust.MarkerModule",
            model_name_or_path="example-org/untrusted-embeddings",
            trust_remote_code=None,
        )
    )

    assert not marker.exists(), "the class named by the repository configuration was imported"
    assert exc is not None, "the load was expected to refuse"


def test_untrusted_module_class_from_an_existing_file_path(tmp_path, monkeypatch):
    """A location that exists on this machine but is a file, not a model directory, is not a
    reason to import configuration-selected code."""
    marker = install_probe(tmp_path, monkeypatch, "probe_file_path", MODULE_CLASS)
    existing_file = tmp_path / "example-org-model"
    existing_file.write_text("not a model")

    # Keep the check hermetic: a file path is not turned into a Hub request in this test.
    def no_dynamic_loading(*args, **kwargs):
        raise OSError("no modeling file next to this location")

    monkeypatch.setattr(
        "transformers.dynamic_module_utils.get_class_from_dynamic_module", no_dynamic_loading
    )

    _, exc = run_capture(
        lambda: import_module_class(
            "probe_file_path.MarkerModule",
            model_name_or_path=str(existing_file),
            trust_remote_code=False,
        )
    )

    assert not marker.exists(), "the class named by the configuration was imported"
    assert exc is not None, "the load was expected to refuse"


def test_untrusted_module_class_through_the_cross_encoder_loader(tmp_path, monkeypatch):
    """The same saved configuration reaches the class resolution through another model family."""
    marker = install_probe(tmp_path, monkeypatch, "probe_cross_encoder", MODULE_CLASS)
    model_dir = _saved_modules_dir(
        tmp_path, "probe_cross_encoder", "0_probe", model_type="CrossEncoder"
    )

    _, exc = run_capture(lambda: CrossEncoder(str(model_dir), local_files_only=True))

    assert not marker.exists(), "the class named by the saved model was imported"
    assert exc is not None, "the load was expected to refuse"
