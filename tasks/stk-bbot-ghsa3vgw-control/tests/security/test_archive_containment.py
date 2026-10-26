"""Expanding an untrusted archive must not write outside the archive's own extraction folder."""
from pathlib import Path

from support.archives import tar_bytes, write_tar
from support.harness import created_since, load_module, make_event, new_scan, run, snapshot

UNARCHIVE = ("bbot.modules.internal.unarchive", "unarchive")


def _extract_archive(archive_path, scan):
    module = load_module(*UNARCHIVE, scan)
    run(module.setup())
    event = make_event(scan, {"path": str(archive_path)}, "FILESYSTEM", ["file"])
    assert event.data.get("compression") in {"tar", "zip"}, "the fixture is not a compressed file the module handles"
    run(module.handle_event(event))


def _assert_nothing_outside(tmp_path, victim, before):
    assert not victim.exists() or not any(p.is_file() for p in victim.rglob("*")), (
        "the archive wrote a file outside its extraction folder"
    )
    new_files = [p for p in created_since(tmp_path, before) if Path(p).is_file()]
    stray = [p for p in new_files if Path(p).parent == Path(tmp_path)]
    assert not stray, f"files were created outside the extraction folder: {stray}"


def _tar_pair(tmp_path, link_target, depth=1):
    inner = tar_bytes("payload.txt", b"outside-content")
    pair = tmp_path / "pair.tar"
    write_tar(pair, [("a", None, link_target), ("a.tar", inner)])
    if depth == 1:
        return pair
    outer = tmp_path / "drop.tar"
    write_tar(outer, [("b.tar", pair.read_bytes())])
    pair.unlink()
    return outer


def test_tar_link_cannot_write_into_an_absolute_target(tmp_path):
    victim = tmp_path / "victim"
    victim.mkdir()
    archive = _tar_pair(tmp_path, str(victim))
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract_archive(archive, scan)
    _assert_nothing_outside(tmp_path, victim, before)


def test_tar_link_cannot_write_into_a_relative_target(tmp_path):
    victim = tmp_path / "victim"
    victim.mkdir()
    # the link lives one level below tmp_path, so ../victim leaves the extraction folder
    archive = _tar_pair(tmp_path, "../victim")
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract_archive(archive, scan)
    _assert_nothing_outside(tmp_path, victim, before)


def test_tar_link_cannot_escape_from_a_nested_extraction(tmp_path):
    victim = tmp_path / "victim"
    victim.mkdir()
    archive = _tar_pair(tmp_path, str(victim), depth=2)
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract_archive(archive, scan)
    _assert_nothing_outside(tmp_path, victim, before)


def test_tar_link_cannot_escape_a_nested_extraction_by_relative_target(tmp_path):
    victim = tmp_path / "victim"
    victim.mkdir()
    # the link lives two levels below tmp_path, so ../../victim leaves the extraction folder
    archive = _tar_pair(tmp_path, "../../victim", depth=2)
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract_archive(archive, scan)
    _assert_nothing_outside(tmp_path, victim, before)
