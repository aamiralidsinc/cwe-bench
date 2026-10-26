"""Installing from a crafted root filesystem archive must stay inside the container."""
import os
import stat

import helpers


def test_absolute_link_write_stays_inside_container(pdenv):
    outside = pdenv.outside
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("s", "shared", str(outside)),
        ("f", "shared/pwn", b"MARKER-ABSOLUTE"),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("install", str(archive), "-n", "demo")

    assert helpers.snapshot(outside) == before, (
        "the install created or changed a file outside the container"
    )
    clamped = pdenv.rootfs("demo") / str(outside).lstrip("/") / "pwn"
    assert helpers.read_bytes(clamped) == b"MARKER-ABSOLUTE", (
        "the entry was not materialised inside the container at the path the link names"
    )


def test_relative_ascending_link_write_stays_inside_container(pdenv):
    outside = pdenv.outside
    rootfs = pdenv.rootfs("demo")
    relative = os.path.relpath(outside, rootfs)
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("s", "shared", relative),
        ("f", "shared/pwn", b"MARKER-RELATIVE"),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("install", str(archive), "-n", "demo")

    assert helpers.snapshot(outside) == before, (
        "the install created or changed a file outside the container"
    )
    clamped_parts = [p for p in relative.split("/") if p not in ("..", "", ".")]
    landed = rootfs.joinpath(*clamped_parts, "pwn")
    assert helpers.read_bytes(landed) == b"MARKER-RELATIVE", (
        "the entry was not materialised inside the container"
    )


def test_directory_entry_over_planted_link_stays_inside_container(pdenv):
    outside = pdenv.outside
    victim = outside / "victim"
    victim.mkdir()
    os.chmod(victim, 0o755)
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("s", "shared", str(victim)),
        ("d", "shared", 0o700),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("install", str(archive), "-n", "demo")

    assert helpers.snapshot(outside) == before, (
        "a directory entry acted on the target of a planted link outside the container"
    )
    inside = pdenv.rootfs("demo") / "shared"
    assert inside.is_dir() and not inside.is_symlink(), (
        "the directory entry did not replace the planted link inside the container"
    )
    assert stat.S_IMODE(os.stat(inside).st_mode) == 0o700, (
        "the directory's archived mode was not applied inside the container"
    )
