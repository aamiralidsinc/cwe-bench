#!/usr/bin/env python3
"""Behavioural checks: the legitimate temporary-working-location paths keep working."""
import os
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HID = os.path.dirname(HERE)
WS = os.path.dirname(HID)
HARNESS = os.path.join(HID, "build", "bin", "harness")
SIDTEST = os.path.join(HID, "build", "bin", "sidtest")
RUBY = "ruby"


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def write_junit(path, suite, cases):
    bad = sum(1 for _n, s, _m in cases if s != "pass")
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<testsuite name="%s" tests="%d" failures="%d" errors="0" skipped="0">'
           % (esc(suite), len(cases), bad)]
    for name, status, msg in cases:
        out.append('  <testcase classname="%s" name="%s">' % (esc(suite), esc(name)))
        if status != "pass":
            head = (msg.splitlines() or ["failed"])[0]
            out.append('    <failure message="%s">%s</failure>' % (esc(head), esc(msg)))
        out.append('  </testcase>')
    out.append('</testsuite>')
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def cleanup(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            p = os.path.join(root, d)
            if not os.path.islink(p):
                try:
                    os.chmod(p, 0o700)
                except OSError:
                    pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), 0o600)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)


def base_dir():
    return tempfile.mkdtemp(prefix="passenger-func.", dir="/tmp")


def make_dir(path, mode=0o755):
    os.makedirs(path)
    os.chmod(path, mode)


def run_harness(mode, *args):
    p = subprocess.run([HARNESS, mode] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=180)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_ruby(script, *args):
    p = subprocess.run([RUBY, os.path.join(HERE, script)] + list(args),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def func_instance_fresh_create_and_reuse():
    base = base_dir()
    try:
        parent = os.path.join(base, "temp")
        make_dir(parent)
        inst = os.path.join(parent, "passenger.1.0.11")
        rc, out = run_harness("gen", inst)
        assert rc == 0, "creating a generation in a fresh location failed: %s" % out.strip()[-300:]
        gen0 = os.path.join(inst, "generation-0")
        assert os.path.isdir(gen0), "generation-0 was not created"
        assert os.path.isfile(os.path.join(gen0, "structure_version.txt")), \
            "generation structure file missing"
        assert os.path.isdir(os.path.join(gen0, "backends")), "backends directory missing"
        assert os.path.isdir(os.path.join(gen0, "buffered_uploads")), \
            "buffered_uploads directory missing"
        st = os.stat(inst)
        assert st.st_uid == os.geteuid(), "wrong owner on the new working directory"
        assert stat.S_IMODE(st.st_mode) == 0o755, "wrong mode on the new working directory"
        rc, out = run_harness("gen", inst)
        assert rc == 0, "reusing the existing working directory failed: %s" % out.strip()[-300:]
        assert os.path.isdir(os.path.join(inst, "generation-1")), \
            "the next generation was not created"
    finally:
        cleanup(base)


def func_instance_reuse_existing_correct_dir():
    base = base_dir()
    try:
        parent = os.path.join(base, "temp")
        make_dir(parent)
        inst = os.path.join(parent, "passenger.1.0.12")
        make_dir(inst)
        rc, out = run_harness("construct", inst)
        assert rc == 0, "an existing correctly-owned directory was refused: %s" % out.strip()[-300:]
        rc, out = run_harness("gen", inst)
        assert rc == 0, "creating a generation in the reused directory failed: %s" % out.strip()[-300:]
        assert os.path.isdir(os.path.join(inst, "generation-0")), "generation-0 was not created"
    finally:
        cleanup(base)


def func_instance_symlinked_parent():
    base = base_dir()
    try:
        parent = os.path.join(base, "real")
        make_dir(parent)
        link = os.path.join(base, "parent-link")
        os.symlink(parent, link)
        inst = os.path.join(link, "passenger.1.0.13")
        rc, out = run_harness("gen", inst)
        assert rc == 0, "a temporary root reached through a link was refused: %s" % out.strip()[-300:]
        assert os.path.isdir(os.path.join(parent, "passenger.1.0.13", "generation-0")), \
            "the generation was not created in the real temporary root"
    finally:
        cleanup(base)


def func_ruby_tmpdir_creates_and_reuses():
    base = base_dir()
    try:
        rc, out = run_ruby("rb_tmpdir_func.rb", WS, base)
        assert rc == 0, "the helper failed: %s" % out.strip()[-300:]
        assert "DIR=true" in out and "UIDOK=true" in out, "the created path is not a directory we own"
        assert "REUSED=true" in out, "an existing working directory was not reused"
        assert "SUBDIRS=true" in out, "the subdirectories were not created"
    finally:
        cleanup(base)


def func_ruby_tmpdir_no_create():
    base = base_dir()
    try:
        rc, out = run_ruby("rb_tmpdir_nocreate.rb", WS, base)
        assert rc == 0, "the helper failed: %s" % out.strip()[-300:]
        assert "EXISTS=false" in out, "asking not to create still created the directory"
    finally:
        cleanup(base)


def func_tmpexedir_usable():
    base = base_dir()
    try:
        rc, out = run_ruby("rb_tmpexedir_func.rb", WS, base)
        assert rc == 0, "the helper failed: %s" % out.strip()[-300:]
        assert "EXEC=yes" in out, "the returned directory cannot execute files"
        assert "DIRWRITABLE=true" in out, "the returned directory is not writable"
    finally:
        cleanup(base)


def func_project_server_instance_dir_tests():
    base = base_dir()
    try:
        p = subprocess.run([SIDTEST], cwd=base, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        out = p.stdout.decode("utf-8", "replace")
        assert p.returncode == 0, "the project's own test group failed: %s" % out.strip()[-500:]
        assert "ok:13" in out, "the project's own test group did not report all cases: %s" % out.strip()[-300:]
    finally:
        cleanup(base)


CASES = [
    ("func_instance_fresh_create_and_reuse", func_instance_fresh_create_and_reuse),
    ("func_instance_reuse_existing_correct_dir", func_instance_reuse_existing_correct_dir),
    ("func_instance_symlinked_parent", func_instance_symlinked_parent),
    ("func_ruby_tmpdir_creates_and_reuses", func_ruby_tmpdir_creates_and_reuses),
    ("func_ruby_tmpdir_no_create", func_ruby_tmpdir_no_create),
    ("func_tmpexedir_usable", func_tmpexedir_usable),
    ("func_project_server_instance_dir_tests", func_project_server_instance_dir_tests),
]


def main():
    out_path = sys.argv[1]
    cases = []
    for name, fn in CASES:
        try:
            fn()
            cases.append((name, "pass", ""))
        except Exception as e:  # noqa: BLE001
            cases.append((name, "fail", "%s: %s" % (type(e).__name__, e)))
    write_junit(out_path, "functional", cases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
