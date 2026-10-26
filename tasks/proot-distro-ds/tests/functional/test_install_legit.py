"""Legitimate installs keep working."""
import os

import helpers


def test_install_keeps_links_and_hardlinks(pdenv):
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("d", "usr/lib"),
        ("f", "usr/lib/marker", b"INSIDE"),
        ("s", "lib", "usr/lib"),
        ("f", "lib/extra", b"THROUGH-RELATIVE-LINK"),
        ("d", "run"),
        ("d", "var"),
        ("s", "var/run", "/run"),
        ("f", "a", b"LINKED-BODY"),
        ("l", "b", "a"),
    ])

    result = pdenv.run("install", str(archive), "-n", "demo")

    assert result.returncode == 0, result.stderr[-800:]
    rootfs = pdenv.rootfs("demo")
    assert helpers.read_bytes(rootfs / "usr/lib/extra") == b"THROUGH-RELATIVE-LINK"
    assert os.readlink(rootfs / "lib") == "usr/lib"
    assert os.readlink(rootfs / "var/run") == "/run"
    assert helpers.read_bytes(rootfs / "b") == b"LINKED-BODY"
    assert helpers.snapshot(pdenv.outside) == {}


def test_install_writes_container_configuration(pdenv):
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "etc"),
        ("f", "etc/passwd", b"root:x:0:0:root:/root:/bin/sh\n"),
        ("f", "etc/resolv.conf", b"nameserver 9.9.9.9\n"),
        ("d", "usr"),
    ])

    result = pdenv.run("install", str(archive), "-n", "demo")

    assert result.returncode == 0, result.stderr[-800:]
    rootfs = pdenv.rootfs("demo")
    resolv = (rootfs / "etc/resolv.conf").read_text()
    assert "8.8.8.8" in resolv
    assert (rootfs / "etc/hosts").is_file()
    assert helpers.snapshot(pdenv.outside) == {}
