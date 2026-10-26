"""Hard links inside an added archive must not read outside the staging root."""
import helpers

SECRET = b"HOST-SECRET-MARKER\n"


def test_added_archive_hardlink_does_not_read_outside(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "secret", SECRET)
    context = pdenv.root / "add-context"
    context.mkdir()
    archive = context / "layer.tar"
    helpers.make_tar(archive, [
        ("s", "shared", str(outside)),
        ("l", "stolen", "shared/secret"),
    ])
    (context / "Dockerfile").write_text(
        "FROM scratch\nADD layer.tar /\n"
    )
    before = helpers.snapshot(outside)

    pdenv.run(
        "build", str(context), "-t", "built:latest", "--install-as", "built", "-q"
    )

    assert helpers.snapshot(outside) == before
    stolen = pdenv.rootfs("built") / "stolen"
    assert SECRET not in helpers.read_bytes(stolen), (
        "a file from outside the container was read into the image"
    )
