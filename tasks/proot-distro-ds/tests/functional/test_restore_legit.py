"""Legitimate backups and restores keep working."""
import os
import stat

import helpers


def _normal_rootfs(pdenv):
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "etc"),
        ("f", "etc/passwd", b"root:x:0:0:root:/root:/bin/sh\n"),
        ("d", "usr"),
        ("d", "usr/lib"),
        ("f", "usr/lib/marker", b"INSIDE"),
        ("s", "lib", "usr/lib"),
        ("f", "lib/extra", b"THROUGH-RELATIVE-LINK"),
    ])
    result = pdenv.run("install", str(archive), "-n", "demo")
    assert result.returncode == 0, result.stderr[-800:]


def test_backup_and_restore_round_trip(pdenv):
    _normal_rootfs(pdenv)
    backup = pdenv.root / "demo-backup.tar"
    result = pdenv.run("backup", "demo", "-o", str(backup))
    assert result.returncode == 0, result.stderr[-800:]

    result = pdenv.run("restore", str(backup))

    assert result.returncode == 0, result.stderr[-800:]
    rootfs = pdenv.rootfs("demo")
    assert helpers.read_bytes(rootfs / "usr/lib/extra") == b"THROUGH-RELATIVE-LINK"
    assert helpers.read_bytes(rootfs / "usr/lib/marker") == b"INSIDE"
    assert os.readlink(rootfs / "lib") == "usr/lib"
    assert (rootfs / "etc/hosts").is_file()
    assert "8.8.8.8" in (rootfs / "etc/resolv.conf").read_text()
    assert helpers.snapshot(pdenv.outside) == {}


def test_restore_applies_archived_directory_modes(pdenv):
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "demo/rootfs/"),
        ("d", "demo/rootfs/private", 0o500),
        ("f", "demo/rootfs/private/secret", b"PRIVATE"),
        ("d", "demo/rootfs/etc"),
        ("f", "demo/rootfs/etc/passwd", b"root:x:0:0:root:/root:/bin/sh\n"),
    ])

    result = pdenv.run("restore", str(archive))

    assert result.returncode == 0, result.stderr[-800:]
    rootfs = pdenv.rootfs("demo")
    assert helpers.read_bytes(rootfs / "private/secret") == b"PRIVATE"
    assert stat.S_IMODE(os.stat(rootfs / "private").st_mode) == 0o500


def test_restore_accepts_legacy_layout(pdenv):
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "installed-rootfs/demo/"),
        ("d", "installed-rootfs/demo/etc"),
        ("f", "installed-rootfs/demo/etc/passwd", b"root:x:0:0:root:/root:/bin/sh\n"),
        ("d", "installed-rootfs/demo/usr"),
        ("f", "installed-rootfs/demo/usr/marker", b"LEGACY"),
    ])

    result = pdenv.run("restore", str(archive))

    assert result.returncode == 0, result.stderr[-800:]
    rootfs = pdenv.rootfs("demo")
    assert helpers.read_bytes(rootfs / "usr/marker") == b"LEGACY"
