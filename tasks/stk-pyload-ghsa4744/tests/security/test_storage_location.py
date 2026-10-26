"""The download folder must never resolve into the service's own temporary working area.  An
account that holds the settings permission but is not an administrator tries to point it there
through the product's own API; the value must not take effect."""
import os

import pytest


def _attempt(env, value):
    before = env.value("general", "storage_folder")
    env.set_value("general", "storage_folder", value)
    return before, env.value("general", "storage_folder")


def test_download_folder_cannot_be_the_temporary_area(env):
    before, after = _attempt(env, env.tempdir)
    assert after == before, f"download folder became {after!r}"


@pytest.mark.parametrize("subdir", ["flask", "jinja", "downloads"])
def test_download_folder_cannot_be_inside_the_temporary_area(env, subdir):
    target = os.path.join(env.tempdir, subdir)
    before, after = _attempt(env, target)
    assert after == before, f"download folder became {after!r}"


def test_download_folder_cannot_resolve_into_the_temporary_area(env):
    holder = env.scratch("indirect")
    link = os.path.join(holder, "downloads")
    os.symlink(env.tempdir, link)
    before, after = _attempt(env, link)
    assert after == before, f"download folder became {after!r}"
