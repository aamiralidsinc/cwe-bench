"""Hidden security tests: install must not create or write through a symbolic
link that stands where the destination's directories have to be created.

Every test drives the real CLI binary built from /app.  The victim tree is
described with plain filesystem calls from the test itself (never with product
code), and the assertions accept either a clean refusal or a safe install at
the named path: what matters is that the link target is untouched.
"""

import os
import subprocess

INSTALL = "/workspace/target/debug/install"


def run_install(args, cwd):
    return subprocess.run(
        [INSTALL, *args], cwd=str(cwd), capture_output=True, text=True, timeout=60
    )


def snapshot(root):
    """Describe everything below root without following symbolic links."""
    state = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in sorted(dirnames + filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            info = os.lstat(path)
            if os.path.islink(path):
                state[rel] = ("link", os.readlink(path))
            elif os.path.isdir(path):
                state[rel] = ("dir", info.st_mode & 0o7777)
            else:
                with open(path, "rb") as handle:
                    state[rel] = ("file", info.st_mode & 0o7777, handle.read())
    return state


def make_workspace(tmp_path):
    base = tmp_path / "base"
    victim = tmp_path / "victim"
    base.mkdir()
    (victim / "sub").mkdir(parents=True)
    (victim / "keep.txt").write_text("important data")
    (victim / "payload").write_text("original payload")
    (victim / "sub" / "keep.txt").write_text("important data")
    source = tmp_path / "source"
    source.write_text("new payload")
    return base, victim, source


def assert_blocked(result, victim, before):
    after = snapshot(victim)
    assert after == before, (
        "the symbolic link target was modified: "
        f"before={before!r} after={after!r}"
    )
    if result.returncode != 0:
        assert result.stderr.strip(), "the command failed without a diagnostic"
        assert "panicked at" not in result.stderr.lower(), (
            "the command crashed instead of refusing cleanly"
        )


def test_missing_parent_directories_are_not_created_through_link(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", str(source), str(base / "link" / "new" / "payload")], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "link" / "new" / "payload"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"


def test_destination_directory_that_is_a_link_is_not_used(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", str(source), str(base / "link" / "payload")], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        assert (base / "link").is_dir() and not (base / "link").is_symlink()
        assert (base / "link" / "payload").read_text() == "new payload"


def test_relative_destination_does_not_create_through_link(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", str(source), "link/new/payload"], base)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "link" / "new" / "payload"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"


def test_link_below_an_existing_ancestor_is_not_created_through(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    (base / "existing").mkdir()
    os.symlink(victim, base / "existing" / "link")
    before = snapshot(victim)

    result = run_install(
        ["-D", str(source), str(base / "existing" / "link" / "new" / "payload")], tmp_path
    )

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "existing" / "link" / "new" / "payload"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"


def test_target_directory_path_is_not_created_through_link(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", "-t", str(base / "link" / "new"), str(source)], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "link" / "new" / "source"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"


def test_existing_target_directory_link_is_not_used(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", "-t", str(base / "link"), str(source)], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        assert (base / "link").is_dir() and not (base / "link").is_symlink()
        assert (base / "link" / "source").read_text() == "new payload"


def test_directory_mode_does_not_create_through_link(tmp_path):
    base, victim, _source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-d", str(base / "link" / "new")], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        created = base / "link" / "new"
        assert created.is_dir() and not created.is_symlink()


def test_directory_mode_nested_creation_does_not_follow_link(tmp_path):
    base, victim, _source = make_workspace(tmp_path)
    (base / "existing").mkdir()
    os.symlink(victim, base / "existing" / "link")
    before = snapshot(victim)

    result = run_install(["-d", str(base / "existing" / "link" / "new" / "deeper")], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        created = base / "existing" / "link" / "new" / "deeper"
        assert created.is_dir() and not created.is_symlink()


def test_existing_destination_link_is_not_moved_by_backup(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    destination = tmp_path / "destination"
    os.symlink(victim / "keep.txt", destination)
    before = snapshot(victim)

    result = run_install(["-b", str(source), str(destination)], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        assert destination.is_file() and not destination.is_symlink()
        assert destination.read_text() == "new payload"


def test_existing_destination_directory_link_is_not_used(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", str(source), str(base / "link")], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "link"
        assert installed.is_dir() and not installed.is_symlink()
        assert (installed / "source").read_text() == "new payload"


def test_existing_destination_directory_link_with_separator_is_not_used(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install(["-D", str(source), str(base / "link") + "/"], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "link"
        assert installed.is_dir() and not installed.is_symlink()
        assert (installed / "source").read_text() == "new payload"


def test_multiple_sources_do_not_write_through_destination_directory_link(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    second = tmp_path / "second"
    second.write_text("second payload")
    os.symlink(victim, base / "link")
    before = snapshot(victim)

    result = run_install([str(source), str(second), str(base / "link")], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = base / "link"
        assert installed.is_dir() and not installed.is_symlink()
        assert (installed / "source").read_text() == "new payload"
        assert (installed / "second").read_text() == "second payload"


def test_target_directory_existing_destination_link_is_not_followed(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    out = base / "out"
    out.mkdir()
    os.symlink(victim / "keep.txt", out / "source")
    before = snapshot(victim)

    result = run_install(["-D", "-t", str(out), str(source)], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = out / "source"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"


def test_multiple_sources_existing_destination_link_is_not_followed(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    second = tmp_path / "second"
    second.write_text("second payload")
    out = base / "out"
    out.mkdir()
    os.symlink(victim / "keep.txt", out / "source")
    before = snapshot(victim)

    result = run_install([str(source), str(second), str(out)], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = out / "source"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"
        assert (out / "second").read_text() == "second payload"


def test_existing_directory_destination_link_is_not_followed(tmp_path):
    base, victim, source = make_workspace(tmp_path)
    out = base / "out"
    out.mkdir()
    os.symlink(victim / "keep.txt", out / "source")
    before = snapshot(victim)

    result = run_install(["-D", str(source), str(out)], tmp_path)

    assert_blocked(result, victim, before)
    if result.returncode == 0:
        installed = out / "source"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_text() == "new payload"
