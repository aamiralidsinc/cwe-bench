from __future__ import annotations

import os
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError

import pytest

# The restored project has no generated version file and no installed metadata: virtualenv is imported straight
# from its source tree. Provide both so entry-point discovery and imports behave as in a normal install.
if "virtualenv.version" not in sys.modules:
    _version = types.ModuleType("virtualenv.version")
    _version.__version__ = "0.0.0"
    sys.modules["virtualenv.version"] = _version


def _install_metadata() -> None:
    import tomllib

    workspace = Path(os.environ.get("VIRTUALENV_WORKSPACE", "/workspace"))
    target = Path(tempfile.mkdtemp(prefix="virtualenv-ep-")) / "virtualenv-0.0.0.dist-info"
    target.mkdir(parents=True)
    (target / "METADATA").write_text("Metadata-Version: 2.1\nName: virtualenv\nVersion: 0.0.0\n", encoding="utf-8")
    try:
        data = tomllib.loads((workspace / "pyproject.toml").read_text(encoding="utf-8"))
        groups = data.get("project", {}).get("entry-points", {})
    except Exception:  # noqa: BLE001 - a missing/unreadable pyproject just means no entry points
        groups = {}
    lines = []
    for group, entries in groups.items():
        lines.append(f"[{group}]")
        for name, value in entries.items():
            lines.append(f"{name} = {' '.join(str(value).split())}")
        lines.append("")
    (target / "entry_points.txt").write_text("\n".join(lines), encoding="utf-8")
    sys.path.insert(0, str(target.parent))


_install_metadata()


def _block_urlopen(monkeypatch: pytest.MonkeyPatch) -> None:
    def _offline(*_args, **_kwargs):
        raise URLError("offline verifier")

    monkeypatch.setattr("urllib.request.urlopen", _offline)
    for module in list(sys.modules.values()):
        name = getattr(module, "__name__", "")
        if name.startswith("virtualenv") and hasattr(module, "urlopen"):
            monkeypatch.setattr(module, "urlopen", _offline)


@pytest.fixture(autouse=True)
def offline_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """No release index is reachable from the verifier; tests install their own stand-in when they need one."""
    _block_urlopen(monkeypatch)


@contextmanager
def change_env_var(key: str, value: str):
    already_set = key in os.environ
    previous = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if already_set:
            os.environ[key] = previous
        else:
            del os.environ[key]


@pytest.fixture(scope="session")
def session_app_data(tmp_path_factory):
    from virtualenv.app_data import AppDataDiskFolder

    folder = tmp_path_factory.mktemp("session-app-data")
    app_data = AppDataDiskFolder(folder=str(folder))
    with change_env_var("VIRTUALENV_OVERRIDE_APP_DATA", str(app_data.lock.path)):
        yield app_data


@pytest.fixture(scope="session")
def for_py_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture
def time_freeze(time_machine):
    return lambda value: time_machine.move_to(value, tick=False)
