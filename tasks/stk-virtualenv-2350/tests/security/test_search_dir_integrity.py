"""A wheel taken from an operator-supplied directory must be the artefact its name claims."""

from __future__ import annotations

from pathlib import Path

from support.helpers import (
    FakePip,
    FakeReleaseIndex,
    build_wheel,
    digest,
    installed_marker,
    install_mock_pip,
    make_creator,
    make_seeder,
    seed,
    use_release_index,
)
from virtualenv.app_data import AppDataDiskFolder


def test_search_dir_wheel_with_wrong_bytes_is_not_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "alphadir"
    good = build_wheel(tmp_path / "published", distribution, "GOOD")
    poison = build_wheel(tmp_path / "offered", distribution, "POISON")
    index = FakeReleaseIndex()
    index.publish(distribution, "9.9.9", good.name, digest(good))
    use_release_index(monkeypatch, index)
    install_mock_pip(monkeypatch, FakePip(returncode=1))
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    creator = make_creator(tmp_path / "venv")
    seed(
        make_seeder(app_data, distribution, extra_search_dir=[poison.parent], download=False),
        creator,
    )

    assert installed_marker(creator, distribution) != "POISON"
