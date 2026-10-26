"""Drive the real Ansible command-line entry points in the restored product tree.

The product root is /workspace. Every invocation gets a private HOME and temp area; no test
reads product code to compute an expected value.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pexpect

PRODUCT = os.environ.get("PRODUCT_ROOT", "/workspace")
PYTHON = sys.executable
MSG_RE = re.compile(r'"msg":\s*"(.*)"')


def _env(home, extra=None):
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": home,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
        "PYTHONPATH": os.path.join(PRODUCT, "lib"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "ANSIBLE_NOCOLOR": "1",
        "ANSIBLE_HOST_KEY_CHECKING": "False",
        "ANSIBLE_LOCAL_TEMP": os.path.join(home, "local"),
        "ANSIBLE_REMOTE_TEMP": os.path.join(home, "remote"),
    }
    if extra:
        env.update(extra)
    return env


def _parse(output):
    match = MSG_RE.search(output or "")
    return match.group(1) if match else None


def _ansible_cmd(arg, extra_args):
    return [os.path.join(PRODUCT, "bin", "ansible"), "localhost", "-m", "debug", "-a", arg] + list(extra_args)


def run_plain(arg="msg={{ ansible_password }}", extra_args=(), extra_env=None, timeout=180):
    """Run the ad-hoc CLI without a prompted secret; return (message, raw output)."""
    home = tempfile.mkdtemp(prefix="ansible-behaviour-")
    try:
        env = _env(home, extra_env)
        proc = subprocess.run(
            [PYTHON] + _ansible_cmd(arg, extra_args),
            cwd=home, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
        )
        out = proc.stdout.decode("utf-8", "replace")
        return _parse(out), out
    finally:
        shutil.rmtree(home, ignore_errors=True)


def run_prompted(password, arg="msg={{ ansible_password }}", extra_args=(), extra_env=None, timeout=180):
    """Run the ad-hoc CLI and answer its connection-password prompt; return (message, raw output)."""
    home = tempfile.mkdtemp(prefix="ansible-behaviour-")
    try:
        env = _env(home, extra_env)
        child = pexpect.spawn(
            PYTHON, _ansible_cmd(arg, list(extra_args) + ["-k"]),
            cwd=home, env=env, encoding="utf-8", timeout=timeout,
        )
        child.expect("SSH password:")
        child.sendline(password)
        child.expect(pexpect.EOF)
        out = child.before or ""
        child.close()
        return _parse(out), out
    finally:
        shutil.rmtree(home, ignore_errors=True)


def write_password_file(directory, content, name="connection-password"):
    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(content.encode("utf-8"))
    return path


def run_project_unit_tests(paths, timeout=300):
    """Run the project's own unit tests for the affected area; return (returncode, output)."""
    home = tempfile.mkdtemp(prefix="ansible-units-")
    try:
        env = _env(home)
        env["PYTHONPATH"] = os.path.join(PRODUCT, "lib") + os.pathsep + os.path.join(PRODUCT, "test")
        proc = subprocess.run(
            [PYTHON, "-m", "pytest"] + list(paths) + ["-q", "-p", "no:cacheprovider"],
            cwd=PRODUCT, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
        )
        return proc.returncode, proc.stdout.decode("utf-8", "replace")
    finally:
        shutil.rmtree(home, ignore_errors=True)
