"""A download folder that lies in the service's own temporary working area must not survive a
start-up, whether it arrives on the command line or in configuration saved earlier.  Each case
runs the product's own start-up entry point in a fresh installation."""
import os

import pytest

from support import harness


def _layout(env, name):
    base = env.scratch(name)
    userdir = os.path.join(base, "user")
    tempdir = os.path.join(base, "tmp")
    os.makedirs(userdir)
    os.makedirs(tempdir)
    return base, userdir, tempdir


def _assert_not_inside_temp(proc, tempdir):
    assert proc.returncode == 0, proc.stdout.decode(errors="replace")[-3000:]
    used = harness.reported_storage_folder(proc)
    assert not harness.resolves_inside(used, tempdir), f"download folder in use is {used!r}"


def test_startup_does_not_adopt_temporary_area_as_download_folder(env):
    base, userdir, tempdir = _layout(env, "startup-temp")
    target = os.path.join(tempdir, "downloads")
    proc = harness.run_startup(userdir, tempdir, storagedir=target)
    _assert_not_inside_temp(proc, tempdir)
    assert not os.path.exists(target), "a download folder was created in the temporary area"


def test_startup_does_not_adopt_saved_temporary_download_folder(env):
    base, userdir, tempdir = _layout(env, "startup-saved")
    target = os.path.join(tempdir, "downloads")
    harness.seed_config(userdir, target)
    proc = harness.run_startup(userdir, tempdir)
    _assert_not_inside_temp(proc, tempdir)
    assert not os.path.exists(target), "a download folder was created in the temporary area"


@pytest.mark.parametrize("subdir", ["", "flask", "jinja"])
def test_startup_does_not_adopt_temporary_area_child(env, subdir):
    base, userdir, tempdir = _layout(env, "startup-child")
    target = os.path.join(tempdir, subdir) if subdir else tempdir
    proc = harness.run_startup(userdir, tempdir, storagedir=target)
    _assert_not_inside_temp(proc, tempdir)
