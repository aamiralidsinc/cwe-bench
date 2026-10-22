"""Hidden functional tests: legitimate install behaviour must keep working.

These drive the real CLI binary built from /app.  They cover the behaviours next
to every protected path: ordinary nested creation, installing into an existing
directory that is reached through a symbolic link prefix, overwriting and
backing up an existing destination, directory creation with a mode, the
target-directory form, and the errors install already reports.
"""

import os
import subprocess

INSTALL = "/workspace/target/debug/install"


def run_install(args, cwd):
    return subprocess.run(
        [INSTALL, *args], cwd=str(cwd), capture_output=True, text=True, timeout=60
    )


def make_source(tmp_path, name="source", content="new payload"):
    source = tmp_path / name
    source.write_text(content)
    return source


def test_nested_directory_creation(tmp_path):
    source = make_source(tmp_path)
    destination = tmp_path / "base" / "a" / "b" / "payload"

    result = run_install(["-D", str(source), str(destination)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert destination.read_text() == "new payload"
    assert (tmp_path / "base" / "a" / "b").is_dir()


def test_install_into_existing_directory(tmp_path):
    source = make_source(tmp_path)
    directory = tmp_path / "dir"
    directory.mkdir()

    result = run_install([str(source), str(directory)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (directory / "source").read_text() == "new payload"


def test_existing_directory_reached_through_link_prefix_keeps_working(tmp_path):
    real = tmp_path / "real"
    (real / "plugins").mkdir(parents=True)
    prefix = tmp_path / "prefix"
    os.symlink(real, prefix)
    source = make_source(tmp_path)
    destination = prefix / "plugins" / "new" / "payload"

    result = run_install(["-D", str(source), str(destination)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (real / "plugins" / "new" / "payload").read_text() == "new payload"
    assert os.path.islink(prefix), "the existing prefix link must be preserved"


def test_overwriting_existing_destination_without_backup(tmp_path):
    source = make_source(tmp_path)
    destination = tmp_path / "destination"
    destination.write_text("old content")

    result = run_install([str(source), str(destination)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert destination.read_text() == "new payload"
    assert not (tmp_path / "destination~").exists()


def test_backup_and_compare_of_regular_destination(tmp_path):
    source = make_source(tmp_path)
    destination = tmp_path / "destination"
    destination.write_text("old content")

    result = run_install(["-b", str(source), str(destination)], tmp_path)
    assert result.returncode == 0, result.stderr
    assert destination.read_text() == "new payload"
    assert (tmp_path / "destination~").read_text() == "old content"

    before = os.stat(destination)
    result = run_install(["-C", str(source), str(destination)], tmp_path)
    assert result.returncode == 0, result.stderr
    after = os.stat(destination)
    assert (before.st_ino, before.st_mtime_ns) == (after.st_ino, after.st_mtime_ns), (
        "an unchanged file must not be copied again"
    )


def test_symlinked_destination_file_is_replaced(tmp_path):
    victim = tmp_path / "victim"
    victim.mkdir()
    important = victim / "keep.txt"
    important.write_text("important data")
    destination = tmp_path / "destination"
    os.symlink(important, destination)
    source = make_source(tmp_path)

    result = run_install([str(source), str(destination)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert not os.path.islink(destination)
    assert destination.read_text() == "new payload"
    assert important.read_text() == "important data"


def test_directory_mode_creates_directories_and_applies_mode(tmp_path):
    directory = tmp_path / "a" / "b" / "c"

    result = run_install(["-d", "-m", "700", str(directory)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert directory.is_dir()
    assert os.stat(directory).st_mode & 0o777 == 0o700

    result = run_install(["-d", str(directory)], tmp_path)
    assert result.returncode == 0, result.stderr


def test_target_directory_installs_every_source(tmp_path):
    first = make_source(tmp_path, "first", "first payload")
    second = make_source(tmp_path, "second", "second payload")
    directory = tmp_path / "out"

    result = run_install(["-D", "-t", str(directory), str(first), str(second)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (directory / "first").read_text() == "first payload"
    assert (directory / "second").read_text() == "second payload"


def test_relative_destination_creation(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    make_source(work)

    result = run_install(["-D", "source", "out/deep/payload"], work)

    assert result.returncode == 0, result.stderr
    assert (work / "out" / "deep" / "payload").read_text() == "new payload"


def test_regular_file_in_directory_path_is_a_clean_error(tmp_path):
    source = make_source(tmp_path)
    base = tmp_path / "base"
    base.mkdir()
    blocker = base / "blocker"
    blocker.write_text("not a directory")
    destination = base / "blocker" / "sub" / "payload"

    result = run_install(["-D", str(source), str(destination)], tmp_path)

    assert result.returncode != 0
    assert result.stderr.strip()
    assert "panicked at" not in result.stderr.lower()
    assert not destination.exists()
    assert blocker.is_file() and blocker.read_text() == "not a directory"


def test_leading_flag_into_existing_directory(tmp_path):
    source = make_source(tmp_path)
    directory = tmp_path / "dir"
    directory.mkdir()

    result = run_install(["-D", str(source), str(directory)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (directory / "source").read_text() == "new payload"


def test_prefix_link_above_existing_directory_keeps_working(tmp_path):
    real = tmp_path / "real"
    (real / "sub").mkdir(parents=True)
    prefix = tmp_path / "prefix"
    os.symlink(real, prefix)
    source = make_source(tmp_path)

    result = run_install(["-D", str(source), str(prefix / "sub")], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (real / "sub" / "source").read_text() == "new payload"
    assert os.path.islink(prefix), "the existing prefix link must be preserved"


def test_reinstall_over_existing_file_in_target_directory_keeps_working(tmp_path):
    source = make_source(tmp_path)
    directory = tmp_path / "out"
    directory.mkdir()
    existing = directory / "source"
    existing.write_text("old content")

    result = run_install(["-D", "-t", str(directory), str(source)], tmp_path)
    assert result.returncode == 0, result.stderr
    assert existing.read_text() == "new payload"

    result = run_install(["-D", "-t", str(directory), "-m", "640", str(source)], tmp_path)
    assert result.returncode == 0, result.stderr
    assert existing.read_text() == "new payload"
    assert os.stat(existing).st_mode & 0o777 == 0o640


def test_reinstall_multiple_sources_over_existing_files(tmp_path):
    first = make_source(tmp_path, "first", "first payload")
    second = make_source(tmp_path, "second", "second payload")
    directory = tmp_path / "out"
    directory.mkdir()
    (directory / "first").write_text("old first")
    (directory / "second").write_text("old second")

    result = run_install([str(first), str(second), str(directory)], tmp_path)

    assert result.returncode == 0, result.stderr
    assert (directory / "first").read_text() == "first payload"
    assert (directory / "second").read_text() == "second payload"


def test_missing_directory_operand_is_not_created(tmp_path):
    source = make_source(tmp_path)

    result = run_install(["-D", str(source), str(tmp_path / "missing") + "/"], tmp_path)

    assert result.returncode != 0
    assert not (tmp_path / "missing").exists()

    second = make_source(tmp_path, "second", "second payload")
    result = run_install(
        ["-D", str(source), str(second), str(tmp_path / "missing_dir")], tmp_path
    )

    assert result.returncode != 0
    assert not (tmp_path / "missing_dir").exists()
