"""Shared harness for the hidden suites.

Builds one product core per test process and drives configuration changes through the product's
own HTTP API with its own authentication, plus the product's real command line entry point for a
start-up with a given download folder.  Everything is local and offline.
"""
import base64
import os
import re
import subprocess
import sys
import tempfile

SETTINGS_PERM = 128
ADD_PERM = 1

USER = "settingsuser"
PASSWORD = "pass123"
ADMIN = "siteadmin"
ADMIN_PASSWORD = "adminpass"


def src_root():
    """Directory that holds the ``pyload`` package (what goes on PYTHONPATH)."""
    import pyload
    return os.path.dirname(os.path.dirname(os.path.abspath(pyload.__file__)))


class Env:
    """One product core, its HTTP clients, and helpers for start-up runs."""

    def __init__(self):
        self.src = src_root()
        #: the product changes the process-wide temporary directory when the core is built;
        #: remember the system one first so the suites can still create scratch directories
        #: outside the product's own area
        self.sys_temp = tempfile.gettempdir()
        tempfile.tempdir = None
        self._cwd = os.getcwd()

        self.base = tempfile.mkdtemp(prefix="pyload-settings-")
        self.userdir = os.path.join(self.base, "user")
        self.tempdir = os.path.join(self.base, "tmp")
        self.storage = os.path.join(self.base, "downloads")
        os.makedirs(self.storage, exist_ok=True)

        from pyload.core import Core

        self.core = Core(self.userdir, self.tempdir, self.storage, debug=0)
        self.core.db.add_user(USER, PASSWORD, role=1, perms=SETTINGS_PERM | ADD_PERM)
        self.core.db.add_user(ADMIN, ADMIN_PASSWORD, role=0, perms=0)
        self.app = self.core.webserver.app
        self.client = self.app.test_client()

    # -- product configuration through the HTTP API ------------------------------------
    @staticmethod
    def _auth(user, password):
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        return {"Authorization": "Basic " + token}

    def set_value(self, category, option, value, section="core", admin=False):
        user, password = (ADMIN, ADMIN_PASSWORD) if admin else (USER, PASSWORD)
        return self.client.post(
            "/api/set_config_value",
            data={
                "category": category,
                "option": option,
                "value": value,
                "section": section,
            },
            headers=self._auth(user, password),
        )

    def value(self, category, option):
        return self.core.config.get(category, option)

    def plugin_value(self, plugin, option):
        return self.core.config.get_plugin(plugin, option)

    # -- scratch space outside the product's temporary area ----------------------------
    def scratch(self, name):
        return tempfile.mkdtemp(prefix=f"{name}-", dir=self.sys_temp)

    def close(self):
        os.chdir(self._cwd)


_ENV = None


def env():
    global _ENV
    if _ENV is None:
        _ENV = Env()
    return _ENV


# -- start-up: the product's own command line entry point ------------------------------

CONFIG_LINE = re.compile(r'(?m)^(\s*folder storage_folder\s*:\s*"[^"]*"\s*=\s*).*$')
CONFIG_READ = re.compile(r'\bfolder storage_folder\s*:\s*"[^"]*"\s*=\s*(.*)$')


def seed_config(userdir, storage_folder):
    """Write the product's saved configuration with the given download folder."""
    settings = os.path.join(userdir, "settings")
    os.makedirs(settings, exist_ok=True)
    default = os.path.join(src_root(), "pyload", "core", "config", "default.cfg")
    with open(default, encoding="utf-8") as fp:
        text = fp.read()
    text, count = CONFIG_LINE.subn(lambda m: m.group(1) + str(storage_folder), text)
    assert count == 1, count
    with open(os.path.join(settings, "pyload.cfg"), "w", encoding="utf-8") as fp:
        fp.write(text)


def saved_storage_folder(userdir):
    """The download folder the product saved in its own configuration file."""
    path = os.path.join(userdir, "settings", "pyload.cfg")
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            match = CONFIG_READ.search(line)
            if match:
                return match.group(1).strip()
    return None


def run_startup(userdir, tempdir, storagedir=None, timeout=180):
    """Run the product's start-up and exit (its dry-run entry point)."""
    argv = [
        sys.executable, "-m", "pyload", "--dry-run",
        "--userdir", userdir, "--tempdir", tempdir, "--pidfile", "",
    ]
    if storagedir is not None:
        argv += ["--storagedir", storagedir]
    child_env = dict(os.environ)
    inherited = child_env.get("PYTHONPATH")
    child_env["PYTHONPATH"] = src_root() + (os.pathsep + inherited if inherited else "")
    return subprocess.run(
        argv, env=child_env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
    )


def resolves_inside(path, directory):
    """True when ``path`` is ``directory`` itself or lies inside it."""
    path = os.path.realpath(os.path.expanduser(str(path)))
    directory = os.path.realpath(os.path.expanduser(str(directory)))
    return path == directory or path.startswith(directory + os.sep)
