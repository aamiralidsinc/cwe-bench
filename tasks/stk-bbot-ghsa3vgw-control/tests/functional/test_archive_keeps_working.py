"""Ordinary archives keep expanding exactly as they do today."""
import os
from pathlib import Path

from support.archives import tar_bytes, write_compressed, write_tar, write_tar_with_hardlink
from support.harness import created_since, load_module, make_event, new_scan, run, snapshot

UNARCHIVE = ("bbot.modules.internal.unarchive", "unarchive")


def _extract(scan, archive_path):
    module = load_module(*UNARCHIVE, scan)
    run(module.setup())
    event = make_event(scan, {"path": str(archive_path)}, "FILESYSTEM", ["file"])
    assert event.data.get("compression") in {"tar", "bz2", "bzip2", "xz", "gzip", "zip"}, (
        "the fixture is not a compressed file the module handles"
    )
    run(module.handle_event(event))
    return module


def _new_top_dirs(tmp_path, before):
    return [Path(p) for p in created_since(tmp_path, before) if Path(p).is_dir() and Path(p).parent == Path(tmp_path)]


def test_nested_archive_keeps_its_layout(tmp_path):
    inner = tar_bytes("payload.txt", b"nested-content")
    archive = tmp_path / "drop.tar"
    write_tar(archive, [("inner.tar", inner)])
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract(scan, archive)
    outputs = _new_top_dirs(tmp_path, before)
    assert len(outputs) == 1, f"expected one extraction folder, got {outputs}"
    extracted = outputs[0] / "inner" / "payload.txt"
    assert extracted.is_file(), "a nested archive no longer expands into its own subfolder"
    assert extracted.read_bytes() == b"nested-content"


def test_a_link_that_stays_inside_is_still_expanded(tmp_path):
    archive = tmp_path / "links.tar"
    write_tar(archive, [("readme.txt", b"readme-content"), ("link", None, "readme.txt")])
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract(scan, archive)
    outputs = _new_top_dirs(tmp_path, before)
    assert len(outputs) == 1, f"expected one extraction folder, got {outputs}"
    folder = outputs[0]
    assert (folder / "readme.txt").read_bytes() == b"readme-content"
    link = folder / "link"
    assert link.is_symlink(), "an ordinary archive link was not extracted"
    assert os.readlink(link) == "readme.txt"


def test_dotfiles_and_subdirectories_are_extracted(tmp_path):
    archive = tmp_path / "content.tar"
    write_tar(
        archive,
        [
            (".env", b"A=1"),
            (".config/settings.toml", b"k = 1"),
            ("nested/deep/file.txt", b"deep"),
            ("plain.txt", b"plain"),
        ],
    )
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract(scan, archive)
    outputs = _new_top_dirs(tmp_path, before)
    assert len(outputs) == 1, f"expected one extraction folder, got {outputs}"
    folder = outputs[0]
    assert (folder / ".env").read_bytes() == b"A=1"
    assert (folder / ".config" / "settings.toml").read_bytes() == b"k = 1"
    assert (folder / "nested" / "deep" / "file.txt").read_bytes() == b"deep"
    assert (folder / "plain.txt").read_bytes() == b"plain"


def test_compressed_tar_streams_are_extracted(tmp_path):
    before = snapshot(tmp_path)
    scan = new_scan()
    for suffix in ("bz2", "xz", "gz"):
        archive = tmp_path / f"stream.{suffix}"
        write_compressed(archive, suffix, "payload.txt", f"content-{suffix}".encode())
        _extract(scan, archive)
    outputs = _new_top_dirs(tmp_path, before)
    assert len(outputs) == 3, f"expected one extraction folder per archive, got {outputs}"
    found = {}
    for folder in outputs:
        payload = folder / "payload.txt"
        assert payload.is_file(), f"a compressed stream no longer expands: {folder}"
        found[payload.read_bytes()] = True
    assert set(found) == {b"content-bz2", b"content-xz", b"content-gz"}


def test_a_hardlink_that_stays_inside_is_still_expanded(tmp_path):
    archive = tmp_path / "hardlinks.tar"
    write_tar_with_hardlink(archive, "payload.txt", "alias.txt", b"hardlink-content")
    before = snapshot(tmp_path)
    scan = new_scan()
    _extract(scan, archive)
    outputs = _new_top_dirs(tmp_path, before)
    assert len(outputs) == 1, f"expected one extraction folder, got {outputs}"
    folder = outputs[0]
    assert (folder / "payload.txt").read_bytes() == b"hardlink-content"
    alias = folder / "alias.txt"
    assert alias.exists(), "an ordinary in-archive hard link was not extracted"
    assert alias.read_bytes() == b"hardlink-content"
