"""Package content that does not match what the index publishes for it must never
be unpacked."""
from helpers import (
    attempt_download,
    make_archive,
    make_downloader,
    package_entry,
    write_index,
)


def _setup(tmp_path, checksum, members=None):
    chosen = tmp_path / "chosen" / "download"
    chosen.mkdir(parents=True)
    archive, unzipped_size = make_archive(tmp_path / "pkg.zip", members=members)
    entry = package_entry(
        archive,
        archive.stat().st_size,
        unzipped_size,
        checksum=checksum,
    )
    index = write_index(tmp_path / "index.xml", [entry])
    return chosen, index


def test_archive_with_wrong_checksum_is_not_unpacked(tmp_path):
    chosen, index = _setup(tmp_path, "0" * 32)
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert not (chosen / "corpora" / "toy" / "marker.txt").exists()


def test_wrong_checksum_blocks_every_member_of_the_archive(tmp_path):
    chosen, index = _setup(
        tmp_path,
        "f" * 32,
        members=[
            ("toy/marker.txt", b"NLTK-BENCH-MARKER"),
            ("toy/sub/second.txt", b"SECOND"),
        ],
    )
    downloader = make_downloader(index, chosen)
    assert attempt_download(downloader, "toy", chosen)
    assert not (chosen / "corpora" / "toy" / "marker.txt").exists()
    assert not (chosen / "corpora" / "toy" / "sub" / "second.txt").exists()
