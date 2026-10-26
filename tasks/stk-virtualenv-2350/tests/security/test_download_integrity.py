"""A downloaded seed wheel must be the artefact its name claims, whichever way pip reports the download."""

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
)
from virtualenv.app_data import AppDataDiskFolder


def _setup(tmp_path: Path, distribution: str, monkeypatch):
    good = build_wheel(tmp_path / "served", distribution, "GOOD")
    poison = build_wheel(tmp_path / "poison", distribution, "POISON")
    assert good.name == poison.name
    index = FakeReleaseIndex()
    index.publish(distribution, "9.9.9", good.name, digest(good))
    from support.helpers import use_release_index

    use_release_index(monkeypatch, index)
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))
    return good, poison, app_data


def test_downloaded_wheel_with_wrong_bytes_is_not_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "alphadl"
    _good, poison, app_data = _setup(tmp_path, distribution, monkeypatch)
    install_mock_pip(monkeypatch, FakePip([(poison.read_bytes(), poison.name)]))

    creator = make_creator(tmp_path / "venv")
    seed(make_seeder(app_data, distribution, download=True), creator)

    assert installed_marker(creator, distribution) != "POISON"


def test_already_downloaded_wheel_with_wrong_bytes_is_not_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "alphaad"
    _good, poison, app_data = _setup(tmp_path, distribution, monkeypatch)
    cached = app_data.house / poison.name
    cached.write_bytes(poison.read_bytes())
    install_mock_pip(monkeypatch, FakePip(output=f"File was already downloaded {cached.resolve()}"))

    creator = make_creator(tmp_path / "venv")
    seed(make_seeder(app_data, distribution, download=True), creator)

    assert installed_marker(creator, distribution) != "POISON"


def test_unreported_download_with_wrong_bytes_is_not_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "alphafb"
    _good, poison, app_data = _setup(tmp_path, distribution, monkeypatch)
    (app_data.house / poison.name).write_bytes(poison.read_bytes())
    install_mock_pip(monkeypatch, FakePip(output=""))

    creator = make_creator(tmp_path / "venv")
    seed(make_seeder(app_data, distribution, download=True), creator)

    assert installed_marker(creator, distribution) != "POISON"
