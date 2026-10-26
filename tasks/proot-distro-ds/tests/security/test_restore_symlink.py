"""Restoring from a crafted backup must stay inside the container."""
import helpers

SECRET = b"HOST-SECRET-MARKER\n"


def test_absolute_link_write_stays_inside_container(pdenv):
    outside = pdenv.outside
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "demo/rootfs/"),
        ("s", "demo/rootfs/shared", str(outside)),
        ("f", "demo/rootfs/shared/pwn", b"MARKER-RESTORE"),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("restore", str(archive))

    assert helpers.snapshot(outside) == before, (
        "the restore created or changed a file outside the container"
    )
    container = pdenv.containers / "demo"
    clamped = container / str(outside).lstrip("/") / "pwn"
    assert helpers.read_bytes(clamped) == b"MARKER-RESTORE", (
        "the entry was not materialised inside the container at the path the link names"
    )


def test_legacy_layout_link_write_stays_inside_container(pdenv):
    outside = pdenv.outside
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "installed-rootfs/demo/"),
        ("s", "installed-rootfs/demo/shared", str(outside)),
        ("f", "installed-rootfs/demo/shared/pwn", b"MARKER-LEGACY"),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("restore", str(archive))

    assert helpers.snapshot(outside) == before, (
        "the restore created or changed a file outside the container"
    )
    container = pdenv.containers / "demo"
    clamped = container / str(outside).lstrip("/") / "pwn"
    assert helpers.read_bytes(clamped) == b"MARKER-LEGACY", (
        "the entry was not materialised inside the container"
    )


def test_hardlink_source_through_planted_link(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "secret", SECRET)
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "demo/rootfs/"),
        ("s", "demo/rootfs/shared", str(outside)),
        ("l", "demo/rootfs/stolen", "demo/rootfs/shared/secret"),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("restore", str(archive))

    assert helpers.snapshot(outside) == before
    stolen = pdenv.rootfs("demo") / "stolen"
    assert SECRET not in helpers.read_bytes(stolen), (
        "a file from outside the container was copied into it"
    )
