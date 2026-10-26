"""Hard links in an archive must not read through a link planted outside the container."""
import helpers

SECRET = b"HOST-SECRET-MARKER\n"


def _install(pdenv, archive):
    pdenv.run("install", str(archive), "-n", "demo")


def test_hardlink_source_through_planted_link(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "secret", SECRET)
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("s", "shared", str(outside)),
        ("l", "stolen", "shared/secret"),
    ])
    before = helpers.snapshot(outside)

    _install(pdenv, archive)

    assert helpers.snapshot(outside) == before
    stolen = pdenv.rootfs("demo") / "stolen"
    assert SECRET not in helpers.read_bytes(stolen), (
        "a file from outside the container was copied into it"
    )


def test_hardlink_planted_after_the_link_member(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "secret", SECRET)
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("l", "stolen", "shared/secret"),
        ("s", "shared", str(outside)),
    ])
    before = helpers.snapshot(outside)

    _install(pdenv, archive)

    assert helpers.snapshot(outside) == before
    stolen = pdenv.rootfs("demo") / "stolen"
    assert SECRET not in helpers.read_bytes(stolen), (
        "a file from outside the container was copied into it"
    )
