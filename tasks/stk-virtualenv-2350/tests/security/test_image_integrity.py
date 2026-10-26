"""What gets installed must come from the authenticated wheel, not from an older image of the same name."""

from __future__ import annotations

from pathlib import Path

from support.helpers import (
    FakeReleaseIndex,
    build_wheel,
    digest,
    installed_marker,
    make_creator,
    make_seeder,
    seed,
    use_release_index,
)
from virtualenv.app_data import AppDataDiskFolder


def test_stale_install_image_from_different_bytes_is_not_used(tmp_path: Path, monkeypatch) -> None:
    distribution = "alphaimg"
    poison = build_wheel(tmp_path / "private", distribution, "POISON")
    good = build_wheel(tmp_path / "published", distribution, "GOOD")
    assert poison.name == good.name
    index = FakeReleaseIndex()
    use_release_index(monkeypatch, index)
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    # A private build with no public release record is legitimate: it is installed and its image is cached.
    first = make_creator(tmp_path / "first")
    seed(make_seeder(app_data, distribution, extra_search_dir=[poison.parent], download=False), first)
    assert installed_marker(first, distribution) == "POISON"

    # The public artefact now exists under the same name with different bytes and must be what gets installed.
    index.publish(distribution, "9.9.9", good.name, digest(good))
    second = make_creator(tmp_path / "second")
    seed(make_seeder(app_data, distribution, extra_search_dir=[good.parent], download=False), second)

    assert installed_marker(second, distribution) != "POISON"
