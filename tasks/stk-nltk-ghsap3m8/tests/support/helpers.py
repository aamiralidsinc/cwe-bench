"""Shared fixtures for the hidden downloader / resource suites.

Nothing here computes an expected value with product code: checksums and sizes are
taken from the files this module writes, and every temporary tree is removed by
pytest.
"""
import hashlib
from pathlib import Path
from xml.sax.saxutils import quoteattr

MARKER = "NLTK-BENCH-MARKER"


def md5_hex(path):
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def make_archive(path, members=None):
    """Write a small zip archive and return (path, total_uncompressed_size)."""
    import zipfile

    if members is None:
        members = [("toy/marker.txt", MARKER.encode())]
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members:
            archive.writestr(name, data)
    return Path(path), sum(len(data) for _, data in members)


def write_index(path, entries):
    parts = ['<?xml version="1.0"?><nltk_data><packages>']
    for entry in entries:
        attrs = " ".join(f"{key}={quoteattr(str(value))}" for key, value in entry.items())
        parts.append(f"<package {attrs}/>")
    parts.append("</packages><collections></collections></nltk_data>")
    Path(path).write_text("".join(parts))
    return Path(path)


def package_entry(archive, archive_size, unzipped_size, **overrides):
    entry = {
        "id": "toy",
        "name": "toy",
        "subdir": "corpora",
        "url": Path(archive).as_uri(),
        "size": archive_size,
        "unzipped_size": unzipped_size,
        "checksum": md5_hex(archive),
        "unzip": "1",
    }
    entry.update(overrides)
    return entry


def make_downloader(index_path, download_dir):
    from nltk.downloader import Downloader

    return Downloader(
        server_index_url=Path(index_path).as_uri(),
        download_dir=str(download_dir),
    )


def attempt_download(downloader, package_id, download_dir):
    """Return True when the download was refused (raised, or did not report success).

    Any error is an acceptable refusal; the tests then assert the absence of the
    side effect.  A success is anything that returns True.
    """
    try:
        result = downloader.download(
            package_id,
            download_dir=str(download_dir),
            quiet=True,
            raise_on_error=True,
        )
    except Exception:  # noqa: BLE001 - every client error is a refusal
        return True
    return result is not True
