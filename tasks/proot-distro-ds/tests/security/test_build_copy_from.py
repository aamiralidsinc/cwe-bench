"""COPY --from must not read through a link planted in the source stage."""
import helpers

SECRET = b"HOST-SECRET-MARKER\n"


def test_copy_from_source_does_not_follow_link(pdenv):
    outside = pdenv.outside
    helpers.write_marker(outside, "secret", SECRET)

    base = pdenv.root / "base-context"
    base.mkdir()
    archive = base / "layer.tar"
    helpers.make_tar(archive, [("s", "opt", str(outside))])
    (base / "Dockerfile").write_text("FROM scratch\nADD layer.tar /\n")
    result = pdenv.run("build", str(base), "-t", "baseimg:latest", "-q")
    assert result.returncode == 0, result.stderr[-800:]

    context = pdenv.root / "copy-context"
    context.mkdir()
    (context / "Dockerfile").write_text(
        "FROM baseimg:latest\nCOPY --from=0 /opt/secret /stolen\n"
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
