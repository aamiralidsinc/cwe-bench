#!/usr/bin/env python3
"""Behavioural checks: a prepared temporary working location must not redirect the product."""
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
    return tempfile.mkdtemp(prefix="passenger-sec.", dir="/tmp")


def run_harness(mode, *args):
    p = subprocess.run([HARNESS, mode] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=180)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_ruby(script, *args):
    p = subprocess.run([RUBY, os.path.join(HERE, script)] + list(args),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def clean_result(rc, out):
    """0 means the call returned; 3 is the driver's clean refusal. A signal or other
    exit is not a refusal."""
    if rc in (0, 3):
        return
    raise AssertionError("the call neither returned nor refused cleanly (exit %r): %s"
                         % (rc, out.strip()[-400:]))


def make_dir(path, mode=0o755):
    os.makedirs(path)
    os.chmod(path, mode)


def prepared_link(base):
    inst = os.path.join(base, "instance", "passenger.1.0.4141")
    target = os.path.join(base, "target")
    make_dir(os.path.dirname(inst))
    make_dir(target)
    os.symlink(target, inst)
    return inst, target


def sec_instance_prepared_link_construct():
    base = base_dir()
    try:
        inst, target = prepared_link(base)
        marker = os.path.join(target, "marker")
        with open(marker, "w") as f:
            f.write("keep")
        os.chmod(marker, 0o400)
        rc, out = run_harness("construct", inst)
        clean_result(rc, out)
        assert stat.S_IMODE(os.stat(marker).st_mode) == 0o400, \
            "a file in the prepared target was re-permissioned"
        with open(marker) as f:
            assert f.read() == "keep", "a file in the prepared target changed"
        if rc == 0:
            assert not os.path.islink(inst), \
                "the call kept using an entry that is not a real directory"
    finally:
        cleanup(base)


def sec_instance_prepared_link_generation():
    base = base_dir()
    try:
        inst, target = prepared_link(base)
        rc, out = run_harness("gen", inst)
        clean_result(rc, out)
        assert os.listdir(target) == [], "the prepared target received working files"
        if rc == 0:
            st = os.lstat(inst)
            assert stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid(), \
                "the call kept using an entry it does not own"
    finally:
        cleanup(base)


def sec_instance_swap_before_generation():
    base = base_dir()
    try:
        inst = os.path.join(base, "instance")
        target = os.path.join(base, "target")
        make_dir(inst)
        make_dir(target)
        rc, out = run_harness("swapgen", inst, target)
        clean_result(rc, out)
        assert os.listdir(target) == [], \
            "files were created in a directory swapped in after the check"
    finally:
        cleanup(base)


def sec_instance_swap_before_destroy():
    base = base_dir()
    try:
        inst = os.path.join(base, "instance")
        target = os.path.join(base, "target")
        make_dir(inst)
        make_dir(target)
        marker = os.path.join(target, "marker")
        with open(marker, "w") as f:
            f.write("keep")
        os.chmod(marker, 0o400)
        os.chmod(target, 0o500)
        rc, out = run_harness("swapdestroy", inst, target)
        clean_result(rc, out)
        assert stat.S_IMODE(os.stat(target).st_mode) == 0o500, \
            "the swapped-in directory was re-permissioned"
        assert stat.S_IMODE(os.stat(marker).st_mode) == 0o400, \
            "a file in the swapped-in directory was re-permissioned"
        with open(marker) as f:
            assert f.read() == "keep", "a file in the swapped-in directory changed"
    finally:
        cleanup(base)


def sec_ruby_tmpdir_prepared_link():
    base = base_dir()
    try:
        rc, out = run_ruby("rb_tmpdir_sec.rb", WS, base)
        assert rc == 0, "the helper failed: %s" % out.strip()[-400:]
        assert "TARGET_PROBE=no" in out, \
            "a file written through the returned path landed in the prepared target"
        if "RETURNED" in out:
            assert "RETURNED_IS_DIR=yes" in out, \
                "the call returned a path that is not a real directory"
    finally:
        cleanup(base)


def sec_tmpexedir_prepared_link():
    base = base_dir()
    try:
        rc, out = run_ruby("rb_tmpexedir_sec.rb", WS, base)
        assert rc == 0, "the helper failed: %s" % out.strip()[-400:]
        assert "TARGET=ORIGINAL" in out, "the prepared target was overwritten"
        assert "MODE=644" in out, "the prepared target was re-permissioned"
    finally:
        cleanup(base)


CASES = [
    ("sec_instance_prepared_link_construct", sec_instance_prepared_link_construct),
    ("sec_instance_prepared_link_generation", sec_instance_prepared_link_generation),
    ("sec_instance_swap_before_generation", sec_instance_swap_before_generation),
    ("sec_instance_swap_before_destroy", sec_instance_swap_before_destroy),
    ("sec_ruby_tmpdir_prepared_link", sec_ruby_tmpdir_prepared_link),
    ("sec_tmpexedir_prepared_link", sec_tmpexedir_prepared_link),
]


def main():
    out_path = sys.argv[1]
    cases = []
    for name, fn in CASES:
        try:
            fn()
            cases.append((name, "pass", ""))
        except Exception as e:  # noqa: BLE001 - a failed check is a failed test, never a crash
            cases.append((name, "fail", "%s: %s" % (type(e).__name__, e)))
    write_junit(out_path, "security", cases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
