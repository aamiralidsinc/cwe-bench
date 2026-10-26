"""Installing a package must not create, remove, write or unpack anything outside the
directory the caller chose for the download, even when the install is refused."""
from helpers import (
    attempt_download,
    make_archive,
    make_downloader,
    package_entry,
    write_index,
)


def _setup(tmp_path, **overrides):
    chosen = tmp_path / "chosen" / "download"
    chosen.mkdir(parents=True)
    archive, unzipped_size = make_archive(tmp_path / "pkg.zip")
    entry = package_entry(
        archive,
        archive.stat().st_size,
        unzipped_size,
        **overrides,
    )
    index = write_index(tmp_path / "index.xml", [entry])
    return tmp_path / "chosen", chosen, archive, entry, index


def test_subdir_escape_is_refused_and_creates_nothing_outside(tmp_path):
    base, chosen, _archive, _entry, index = _setup(tmp_path, subdir="../outside")
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert not (base / "outside").exists()


def test_package_id_with_separator_is_refused(tmp_path):
    base, chosen, _archive, _entry, index = _setup(tmp_path, id="../../escaped")
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "../../escaped", chosen)
    assert not (base / "escaped.zip").exists()


def test_package_filename_override_escape_is_refused(tmp_path):
    base, chosen, _archive, _entry, index = _setup(tmp_path, filename="../outside.zip")
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert not (base / "outside.zip").exists()


def test_absolute_subdir_is_refused(tmp_path):
    absolute = tmp_path / "absolute"
    absolute.mkdir()
    _base, chosen, _archive, _entry, index = _setup(tmp_path, subdir=str(absolute))
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert not (absolute / "toy.zip").exists()


def test_refused_download_does_not_remove_file_outside(tmp_path):
    base, chosen, _archive, _entry, index = _setup(tmp_path, filename="../victim.zip")
    victim = base / "victim.zip"
    victim.write_bytes(b"KEEP-ME")
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert victim.exists()
    assert victim.read_bytes() == b"KEEP-ME"


def test_refused_download_does_not_create_directory_outside(tmp_path):
    base, chosen, _archive, _entry, index = _setup(tmp_path, subdir="../newdir")
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert not (base / "newdir").exists()
