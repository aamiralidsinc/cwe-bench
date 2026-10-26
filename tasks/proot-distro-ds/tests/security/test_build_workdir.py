"""A build must not create directories outside the staging root filesystem."""

import helpers


def _build_base(pdenv, outside, tag):
    context = pdenv.root / "base-context"
    context.mkdir()
    archive = context / "layer.tar"
    helpers.make_tar(archive, [("s", "opt", str(outside))])
    (context / "Dockerfile").write_text("FROM scratch\nADD layer.tar /\n")
    result = pdenv.run("build", str(context), "-t", f"{tag}:latest", "-q")
    assert result.returncode == 0, result.stderr[-800:]


def test_workdir_does_not_follow_link_from_base_image(pdenv):
    outside = pdenv.outside
    _build_base(pdenv, outside, "baseimg")
    context = pdenv.root / "workdir-context"
    context.mkdir()
    (context / "Dockerfile").write_text(
        "FROM baseimg:latest\nWORKDIR /opt/sub\n"
    )
    before = helpers.snapshot(outside)

    pdenv.run("build", str(context), "-t", "built:latest", "-q")

    assert helpers.snapshot(outside) == before, (
        "a build step created a directory outside the staging root filesystem"
    )
