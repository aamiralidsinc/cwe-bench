"""Configuration applied after unpacking must stay inside the container."""
import helpers


def test_configuration_writes_through_planted_link(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "hosts", b"ORIGINAL-HOSTS-MARKER\n")
    helpers.write_marker(outside, "passwd", b"ORIGINAL-PASSWD-MARKER\n")
    archive = pdenv.root / "rootfs.tar"
    helpers.make_tar(archive, [
        ("d", "usr"),
        ("d", "bin"),
        ("s", "etc", str(outside)),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("install", str(archive), "-n", "demo")

    assert helpers.snapshot(outside) == before, (
        "post-extraction configuration wrote through a link onto the host"
    )
