"""Legitimate builds keep working."""
import helpers


def test_copy_add_and_added_hardlink(pdenv):
    context = pdenv.root / "context"
    context.mkdir()
    (context / "hello.txt").write_text("hello\n")
    archive = context / "data.tar"
    helpers.make_tar(archive, [
        ("d", "sub/"),
        ("f", "sub/f.txt", b"FILE-BODY"),
        ("l", "sub/h", "sub/f.txt"),
    ])
    (context / "Dockerfile").write_text(
        "FROM scratch\nCOPY hello.txt /hello.txt\nADD data.tar /data/\n"
    )

    result = pdenv.run(
        "build", str(context), "-t", "built:latest", "--install-as", "built", "-q"
    )

    assert result.returncode == 0, result.stderr[-800:]
    rootfs = pdenv.rootfs("built")
    assert (rootfs / "hello.txt").read_text() == "hello\n"
    assert helpers.read_bytes(rootfs / "data/sub/f.txt") == b"FILE-BODY"
    assert helpers.read_bytes(rootfs / "data/sub/h") == b"FILE-BODY"
    assert helpers.snapshot(pdenv.outside) == {}


def test_workdir_created_inside_container(pdenv):
    base = pdenv.root / "base-context"
    base.mkdir()
    (base / "hello.txt").write_text("hello\n")
    (base / "Dockerfile").write_text("FROM scratch\nCOPY hello.txt /hello.txt\n")
    result = pdenv.run("build", str(base), "-t", "baseimg:latest", "-q")
    assert result.returncode == 0, result.stderr[-800:]

    context = pdenv.root / "workdir-context"
    context.mkdir()
    (context / "Dockerfile").write_text(
        "FROM baseimg:latest\nWORKDIR /app/data\n"
    )
    result = pdenv.run(
        "build", str(context), "-t", "built:latest", "--install-as", "built", "-q"
    )

    assert result.returncode == 0, result.stderr[-800:]
    assert (pdenv.rootfs("built") / "app/data").is_dir()


def test_two_stage_copy_from(pdenv):
    base = pdenv.root / "base-context"
    base.mkdir()
    (base / "hello.txt").write_text("hello-stage\n")
    (base / "Dockerfile").write_text("FROM scratch\nCOPY hello.txt /hello.txt\n")
    result = pdenv.run("build", str(base), "-t", "baseimg:latest", "-q")
    assert result.returncode == 0, result.stderr[-800:]

    context = pdenv.root / "copy-context"
    context.mkdir()
    (context / "Dockerfile").write_text(
        "FROM baseimg:latest\nCOPY --from=0 /hello.txt /copied.txt\n"
    )
    result = pdenv.run(
        "build", str(context), "-t", "built:latest", "--install-as", "built", "-q"
    )

    assert result.returncode == 0, result.stderr[-800:]
    assert (pdenv.rootfs("built") / "copied.txt").read_text() == "hello-stage\n"
