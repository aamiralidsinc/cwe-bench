"""Legitimate acquisition routes keep working: authenticated wheels, private indexes and private distributions."""

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


def test_authenticated_wheel_is_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "betagood"
    good = build_wheel(tmp_path / "served", distribution, "GOOD")
    index = FakeReleaseIndex()
    index.publish(distribution, "9.9.9", good.name, digest(good))
    use_release_index(monkeypatch, index)
    install_mock_pip(monkeypatch, FakePip([(good.read_bytes(), good.name)]))
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    creator = make_creator(tmp_path / "venv")
    seed(make_seeder(app_data, distribution, download=True), creator)

    assert installed_marker(creator, distribution) == "GOOD"


def test_configured_private_index_wheel_is_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "betapriv"
    private = build_wheel(tmp_path / "mirror", distribution, "PRIVATE")
    index = FakeReleaseIndex()
    # The public record describes a different artefact; the operator's mirror serves this one.
    index.publish(distribution, "9.9.9", private.name, "0" * 64)
    use_release_index(monkeypatch, index)
    install_mock_pip(monkeypatch, FakePip([(private.read_bytes(), private.name)]))
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    creator = make_creator(tmp_path / "venv")
    seed(
        make_seeder(app_data, distribution, download=True, env={"PIP_INDEX_URL": "https://mirror.internal/simple"}),
        creator,
    )

    assert installed_marker(creator, distribution) == "PRIVATE"


def test_distribution_without_release_record_is_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "betaopen"
    private = build_wheel(tmp_path / "local", distribution, "LOCAL")
    index = FakeReleaseIndex()
    use_release_index(monkeypatch, index)
    install_mock_pip(monkeypatch, FakePip([(private.read_bytes(), private.name)]))
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    creator = make_creator(tmp_path / "venv")
    seed(make_seeder(app_data, distribution, download=True), creator)

    assert installed_marker(creator, distribution) == "LOCAL"
