"""Coupled behaviour that must survive the integrity checks."""

from __future__ import annotations

import os
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
from virtualenv.seed.wheels.acquire import get_wheel
from virtualenv.seed.wheels.periodic_update import add_wheel_to_update_log
from virtualenv.seed.wheels.util import Wheel


def test_recorded_wheel_absent_from_cache_still_resolves(tmp_path, for_py_version) -> None:
    distribution = "betalog"
    cache = tmp_path / "house"
    cache.mkdir()
    wheel_path = build_wheel(cache, distribution, "CACHED")
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))
    add_wheel_to_update_log(Wheel(wheel_path), for_py_version, app_data)
    wheel_path.unlink()  # the metadata survives a cleared download cache

    wheel = get_wheel(distribution, "9.9.9", for_py_version, [], False, app_data, False, os.environ)

    assert wheel is not None
    assert wheel.name == wheel_path.name


def test_private_wheel_name_is_seeded(tmp_path: Path, monkeypatch) -> None:
    distribution = "betadir"
    published = build_wheel(tmp_path / "published", distribution, "PUBLISHED")
    private = build_wheel(tmp_path / "private", distribution, "PRIVATE", build_tag="1")
    assert published.name != private.name
    index = FakeReleaseIndex()
    index.publish(distribution, "9.9.9", published.name, digest(published))
    use_release_index(monkeypatch, index)
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    creator = make_creator(tmp_path / "venv")
    seed(make_seeder(app_data, distribution, extra_search_dir=[private.parent], download=False), creator)

    assert installed_marker(creator, distribution) == "PRIVATE"


def test_unchanged_wheel_reuses_cached_image(tmp_path: Path, monkeypatch) -> None:
    distribution = "betaimg"
    good = build_wheel(tmp_path / "shared", distribution, "GOOD")
    index = FakeReleaseIndex()
    index.publish(distribution, "9.9.9", good.name, digest(good))
    use_release_index(monkeypatch, index)
    app_data = AppDataDiskFolder(folder=str(tmp_path / "app-data"))

    first = make_creator(tmp_path / "first")
    seed(make_seeder(app_data, distribution, extra_search_dir=[good.parent], download=False), first)
    second = make_creator(tmp_path / "second")
    seed(make_seeder(app_data, distribution, extra_search_dir=[good.parent], download=False), second)

    assert installed_marker(first, distribution) == "GOOD"
    assert installed_marker(second, distribution) == "GOOD"
    first_files = sorted(str(p.relative_to(first.purelib)) for p in first.purelib.rglob("*") if p.is_file())
    second_files = sorted(str(p.relative_to(second.purelib)) for p in second.purelib.rglob("*") if p.is_file())
    assert first_files == second_files
