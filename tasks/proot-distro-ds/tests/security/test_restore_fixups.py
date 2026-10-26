"""Configuration applied after a restore must stay inside the container."""
import helpers


def test_restore_configuration_writes_through_planted_link(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "hosts", b"ORIGINAL-HOSTS-MARKER\n")
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "demo/rootfs/"),
        ("d", "demo/rootfs/bin"),
        ("s", "demo/rootfs/etc", str(outside)),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("restore", str(archive))

    assert helpers.snapshot(outside) == before, (
        "post-restore configuration wrote through a link onto the host"
    )
