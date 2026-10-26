from __future__ import annotations

import json
import os
import sys
from pathlib import Path

MARKER_ENV = "CWE_MARKER_FILE"


def probe_source(extra: str) -> str:
    """A harmless probe module: on import it writes a marker file, then defines `extra`."""
    return (
        "import os\n"
        "from pathlib import Path\n"
        "_marker = os.environ.get('CWE_MARKER_FILE')\n"
        "if _marker:\n"
        "    Path(_marker).write_text('imported')\n"
        "\n"
        + extra
    )


def install_probe(tmp_path: Path, monkeypatch, module_name: str, extra: str) -> Path:
    """Put an importable probe module on sys.path; return the path it writes when imported.

    Every test uses a unique module name: a module is imported at most once per process, so a
    shared name would hide a later import attempt behind sys.modules.
    """
    probes = tmp_path / "probes"
    probes.mkdir(parents=True, exist_ok=True)
    (probes / f"{module_name}.py").write_text(probe_source(extra))
    monkeypatch.syspath_prepend(str(probes))
    marker = tmp_path / f"{module_name}.marker"
    if marker.exists():
        marker.unlink()
    monkeypatch.setenv(MARKER_ENV, str(marker))
    return marker


def write_model_dir(root: Path, modules: list[dict], model_type: str = "SentenceTransformer") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "modules.json").write_text(json.dumps(modules))
    (root / "config_sentence_transformers.json").write_text(json.dumps({"model_type": model_type}))


MODULE_CLASS = """
class MarkerModule:
    @classmethod
    def load(cls, *args, **kwargs):
        raise RuntimeError("configuration-selected module was used")
"""

TOKENIZER_CLASS = """
class MarkerTokenizer:
    @classmethod
    def load(cls, *args, **kwargs):
        raise RuntimeError("configuration-selected tokenizer was used")
"""

ACTIVATION_CLASS = """
class MarkerActivation:
    def __init__(self):
        self.name = "marker"

    def __call__(self, value):
        return value
"""

PROCESSOR_CLASS = """
class MarkerProcessor:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        raise RuntimeError("configuration-selected processor was used")
"""


def run_capture(fn):
    """Run fn; return (value, exception). Never lets a refusal abort the test early."""
    try:
        return fn(), None
    except Exception as exc:  # noqa: BLE001 - the refusal type is not part of the contract
        return None, exc
