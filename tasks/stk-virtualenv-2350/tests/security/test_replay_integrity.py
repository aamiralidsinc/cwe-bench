"""A wheel reused from the local cache must still be the artefact its name claims."""

from __future__ import annotations

import os
from pathlib import Path

from support.helpers import FakePip, FakeReleaseIndex, build_wheel, digest, install_mock_pip, use_release_index
from virtualenv.app_data import AppDataDiskFolder
from virtualenv.seed.wheels.acquire import get_wheel


def test_replayed_wheel_with_wrong_bytes_is_not_handed_out(tmp_path: Path, monkeypatch, for_py_version) -> None:
    distribution = "alpharep"
    good = build_wheel(tmp_path / "served", distribution, "GOOD")
    poison = build_wheel(tmp_path / "poison", distribution, "POISON")
    index = FakeReleaseIndex()
    index.publish(distribution, "9.9.9", good.name, digest(good))
    use_release_index(monkeypatch, index)
    install_mock_pip(monkeypatch, FakePip([(good.read_bytes(), good.name)]))
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    acquired = get_wheel(distribution, "9.9.9", for_py_version, [], True, app_data, False, {})
    assert acquired is not None
    assert acquired.name == good.name

    # The bytes behind the recorded name are replaced after they were accepted once.
    (app_data.house / good.name).write_bytes(poison.read_bytes())

    try:
        replayed = get_wheel(distribution, "9.9.9", for_py_version, [], False, app_data, False, {})
    except Exception:  # noqa: BLE001 - a refusal in any form is the intended outcome
        replayed = None

    assert replayed is None or replayed.path.read_bytes() != poison.read_bytes()
