"""A directory mode applied at the end of a restore must not follow a later link."""
import os
import stat

import helpers


def test_deferred_directory_mode_does_not_follow_link(pdenv):
    outside = pdenv.outside
    victim = outside / "victim"
    victim.mkdir()
    os.chmod(victim, 0o755)
    archive = pdenv.root / "backup.tar"
    helpers.make_tar(archive, [
        ("d", "demo/rootfs/"),
        ("d", "demo/rootfs/target", 0o500),
        ("s", "demo/rootfs/target", str(victim)),
    ])
    before = helpers.snapshot(outside)

    pdenv.run("restore", str(archive))

    assert helpers.snapshot(outside) == before, (
        "a restored directory's mode was applied to a target outside the container"
    )
    assert stat.S_IMODE(os.stat(victim).st_mode) == 0o755
