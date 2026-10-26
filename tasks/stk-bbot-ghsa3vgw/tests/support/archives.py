"""Build archive fixtures with the standard library only."""
import gzip
import io
import bz2
import lzma
import tarfile
from pathlib import Path


def tar_bytes(name, data=b"content"):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def write_tar(path, members):
    """members: list of (name, data) or (name, None, link_target) for a symlink."""
    with tarfile.open(path, "w") as archive:
        for member in members:
            name, data = member[0], member[1]
            info = tarfile.TarInfo(name)
            if len(member) == 3:
                info.type = tarfile.SYMTYPE
                info.linkname = member[2]
                archive.addfile(info)
            else:
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))


def write_tar_with_hardlink(path, target_name, link_name, data=b"content"):
    """A regular member plus a hard link to it, both inside the archive."""
    with tarfile.open(path, "w") as archive:
        info = tarfile.TarInfo(target_name)
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
        link = tarfile.TarInfo(link_name)
        link.type = tarfile.LNKTYPE
        link.linkname = target_name
        archive.addfile(link)


def write_link_and_nested(path, link_name, link_target, nested_name, nested_data):
    """A symlink entry plus an archive entry whose stem matches the link name."""
    write_tar(path, [(link_name, None, link_target), (nested_name, nested_data)])


def write_compressed(path, suffix, member_name, data=b"content"):
    """Write a tar stream compressed with the format implied by suffix (bz2/xz/gz)."""
    raw = tar_bytes(member_name, data)
    if suffix == "bz2":
        payload = bz2.compress(raw)
    elif suffix == "xz":
        payload = lzma.compress(raw)
    elif suffix == "gz":
        payload = gzip.compress(raw)
    else:
        payload = raw
    Path(path).write_bytes(payload)
