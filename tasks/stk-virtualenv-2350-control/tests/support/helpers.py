from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace


def build_wheel(folder: Path, distribution: str, marker: str, version: str = "9.9.9", build_tag: str = "") -> Path:
    """Write a small but complete wheel for ``distribution`` whose installed marker is ``marker``."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    tag = f"-{build_tag}" if build_tag else ""
    name = f"{distribution}-{version}{tag}-py3-none-any.whl"
    path = folder / name
    dist_info = f"{distribution}-{version}.dist-info"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{distribution}/__init__.py", f"MARKER = {marker!r}\n")
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.1\nName: {distribution}\nVersion: {version}\n",
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr(f"{dist_info}/RECORD", "")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FakeReleaseIndex:
    """A release index the product can query through urlopen; it publishes digests per (distribution, version)."""

    def __init__(self) -> None:
        self._releases: dict[str, dict[str, list[dict[str, object]]]] = {}

    def publish(self, distribution: str, version: str, filename: str, sha256: str) -> None:
        entry = {"filename": filename, "digests": {"sha256": sha256}}
        self._releases.setdefault(distribution, {}).setdefault(version, []).append(entry)

    def withdraw(self, distribution: str) -> None:
        self._releases.pop(distribution, None)

    def urlopen(self, url, *_args, **_kwargs):
        parts = str(url).rstrip("/").split("/")
        distribution = parts[-2] if len(parts) >= 2 else ""
        body = {"releases": self._releases.get(distribution, {})}
        return io.StringIO(json.dumps(body))


def use_release_index(monkeypatch, index: FakeReleaseIndex) -> None:
    """Point every module's urlopen at the stand-in index (the product imports the name directly)."""
    monkeypatch.setattr("urllib.request.urlopen", index.urlopen)
    for module in list(sys.modules.values()):
        name = getattr(module, "__name__", "")
        if name.startswith("virtualenv") and hasattr(module, "urlopen"):
            monkeypatch.setattr(module, "urlopen", index.urlopen)


class _Process:
    def __init__(self, output: str, returncode: int = 0) -> None:
        self._output = output
        self.returncode = returncode

    def communicate(self):
        return self._output, ""


class FakePip:
    """Stand-in for the pip subprocess: writes the bytes the configured index would serve into ``-d``."""

    def __init__(self, payloads=None, returncode: int = 0, output: str | None = None) -> None:
        # each payload: (bytes, filename); the last one repeats
        self.payloads = list(payloads or [])
        self.returncode = returncode
        self.output = output
        self.calls = 0
        self.targets: list[Path] = []

    def __call__(self, cmd, *_args, **_kwargs):
        folder = Path(cmd[cmd.index("-d") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        if self.returncode != 0 or self.output is not None and not self.payloads:
            return _Process(self.output or "", self.returncode)
        data, filename = self.payloads[min(self.calls, len(self.payloads) - 1)]
        self.calls += 1
        path = folder / filename
        if not path.exists():
            path.write_bytes(data)
        self.targets.append(path)
        return _Process(self.output if self.output is not None else f"Saved {path}", self.returncode)


def install_mock_pip(monkeypatch, pip: FakePip) -> FakePip:
    monkeypatch.setattr("virtualenv.seed.wheels.acquire.Popen", pip)
    return pip


def make_seeder(app_data, distribution: str, extra_search_dir=(), download: bool = False, env=None, version=None):
    from virtualenv.seed.embed.via_app_data.via_app_data import FromAppData

    options = SimpleNamespace(
        no_seed=False,
        download=download,
        extra_search_dir=[Path(entry) for entry in extra_search_dir],
        pip=None,
        setuptools=None,
        wheel=None,
        no_pip=True,
        no_setuptools=True,
        no_wheel=True,
        app_data=app_data,
        no_periodic_update=True,
        symlink_app_data=False,
        env=dict(env or {}),
    )

    class _Seeder(FromAppData):
        def distribution_to_versions(self):
            return {distribution: version}

    return _Seeder(options)


def make_creator(root: Path):
    from python_discovery import PythonInfo

    root = Path(root)
    purelib = root / "purelib"
    platlib = root / "platlib"
    scripts = root / "scripts"
    for folder in (purelib, platlib, scripts):
        folder.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(
        purelib=purelib,
        platlib=platlib,
        script_dir=scripts,
        exe=Path(sys.executable),
        interpreter=PythonInfo.current_system(),
    )


def seed(seeder, creator) -> BaseException | None:
    try:
        seeder.run(creator)
    except BaseException as exception:  # noqa: BLE001 - any refusal form is acceptable to the caller
        return exception
    return None


def installed_marker(creator, distribution: str):
    path = Path(creator.purelib) / distribution / "__init__.py"
    if not path.exists():
        return None
    namespace: dict[str, object] = {}
    exec(path.read_text(encoding="utf-8"), namespace)  # noqa: S102 - test-authored wheel content
    return namespace.get("MARKER")
