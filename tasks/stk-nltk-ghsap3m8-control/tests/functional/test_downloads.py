"""Legitimate package installs inside the caller's chosen location keep working."""
from helpers import (
    MARKER,
    attempt_download,
    make_archive,
    make_downloader,
    package_entry,
    write_index,
)


def _install(tmp_path, download_dir):
    archive, unzipped_size = make_archive(tmp_path / "pkg.zip")
    entry = package_entry(archive, archive.stat().st_size, unzipped_size)
    index = write_index(tmp_path / "index.xml", [entry])
    downloader = make_downloader(index, download_dir)
    return attempt_download(downloader, "toy", download_dir)


def test_normal_package_install_writes_archive_and_extracts(tmp_path):
    chosen = tmp_path / "download"
    chosen.mkdir()
    assert not _install(tmp_path, chosen)
    assert (chosen / "corpora" / "toy.zip").is_file()
    assert (chosen / "corpora" / "toy" / "marker.txt").read_text() == MARKER


def test_install_into_nested_missing_download_dir(tmp_path):
    chosen = tmp_path / "one" / "two" / "three"
    assert not _install(tmp_path, chosen)
    assert (chosen / "corpora" / "toy" / "marker.txt").read_text() == MARKER


def test_second_install_reports_the_package_up_to_date(tmp_path):
    chosen = tmp_path / "download"
    chosen.mkdir()
    assert not _install(tmp_path, chosen)
    assert not _install(tmp_path, chosen)
    assert (chosen / "corpora" / "toy" / "marker.txt").read_text() == MARKER
