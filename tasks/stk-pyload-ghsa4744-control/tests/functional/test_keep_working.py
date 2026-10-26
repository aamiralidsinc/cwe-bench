"""Behaviour that must keep working exactly as today: ordinary settings for non-administrative
accounts, every setting for an administrator, a download folder outside the service's temporary
area, and a start-up that keeps a legitimate one."""
import os

from support import harness


def test_non_admin_can_change_ordinary_download_setting(env):
    env.set_value("download", "max_speed", 1234)
    assert env.value("download", "max_speed") == 1234


def test_non_admin_can_change_ordinary_display_setting(env):
    env.set_value("webui", "theme", "pyplex")
    assert env.value("webui", "theme") == "pyplex"


def test_non_admin_can_change_ordinary_plugin_setting(env):
    env.set_value("AntiVirus", "action", "Delete", section="plugin")
    assert env.plugin_value("AntiVirus", "action") == "Delete"


def test_admin_can_change_protected_settings(env):
    env.set_value("reconnect", "script", "/bin/true", admin=True)
    assert env.value("reconnect", "script") == "/bin/true"

    env.set_value("webui", "ssl_certfile", "/etc/hostname", admin=True)
    assert os.path.realpath(env.value("webui", "ssl_certfile")) == os.path.realpath("/etc/hostname")

    env.set_value("AntiVirus", "avfile", "/bin/true", section="plugin", admin=True)
    assert os.path.realpath(env.plugin_value("AntiVirus", "avfile")) == os.path.realpath("/bin/true")


def test_download_folder_beside_temporary_area_is_accepted(env):
    target = os.path.join(os.path.dirname(env.tempdir), "downloads-alt")
    env.set_value("general", "storage_folder", target, admin=True)
    assert os.path.realpath(env.value("general", "storage_folder")) == os.path.realpath(target)


def test_download_folder_with_similar_name_is_accepted(env):
    target = env.tempdir + "-downloads"
    env.set_value("general", "storage_folder", target, admin=True)
    assert os.path.realpath(env.value("general", "storage_folder")) == os.path.realpath(target)


def _layout(env, name):
    base = env.scratch(name)
    userdir = os.path.join(base, "user")
    tempdir = os.path.join(base, "tmp")
    os.makedirs(userdir)
    os.makedirs(tempdir)
    return base, userdir, tempdir


def test_startup_keeps_legitimate_download_folder(env):
    base, userdir, tempdir = _layout(env, "keep-cli")
    target = os.path.join(base, "downloads")
    proc = harness.run_startup(userdir, tempdir, storagedir=target)
    assert proc.returncode == 0, proc.stdout.decode(errors="replace")[-3000:]
    assert os.path.isdir(target)
    saved = harness.saved_storage_folder(userdir)
    assert os.path.realpath(saved) == os.path.realpath(target)


def test_startup_keeps_saved_legitimate_download_folder(env):
    base, userdir, tempdir = _layout(env, "keep-saved")
    target = os.path.join(base, "downloads")
    harness.seed_config(userdir, target)
    proc = harness.run_startup(userdir, tempdir)
    assert proc.returncode == 0, proc.stdout.decode(errors="replace")[-3000:]
    assert os.path.isdir(target)
    saved = harness.saved_storage_folder(userdir)
    assert os.path.realpath(saved) == os.path.realpath(target)


def test_startup_keeps_download_folder_with_similar_name(env):
    base, userdir, tempdir = _layout(env, "keep-prefix")
    target = tempdir + "-downloads"
    proc = harness.run_startup(userdir, tempdir, storagedir=target)
    assert proc.returncode == 0, proc.stdout.decode(errors="replace")[-3000:]
    assert os.path.isdir(target)
    saved = harness.saved_storage_folder(userdir)
    assert os.path.realpath(saved) == os.path.realpath(target)
