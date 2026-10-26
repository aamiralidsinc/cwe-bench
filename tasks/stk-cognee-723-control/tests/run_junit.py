#!/usr/bin/env python3
"""Run one hidden suite, one test module per process, and write merged JUnit XML.

The application resolves its authentication posture and its public-registration
policy from the process environment when modules are imported, so each test
module is executed in its own fresh interpreter with the posture it needs.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

# Posture shared by every module: single-user deployment, public sign-up on,
# no stored provider keys.  Files that need another posture override it below.
BASE_ENV = {
    "REQUIRE_AUTHENTICATION": "false",
    "ENABLE_BACKEND_ACCESS_CONTROL": "false",
    "LLM_API_KEY": "",
    "VECTOR_DB_KEY": "",
    "ENV": "test",
}

FILE_ENV = {
    "test_registration_policy.py": {
        "REQUIRE_AUTHENTICATION": "true",
        "ENABLE_BACKEND_ACCESS_CONTROL": "true",
    },
    "test_settings_multi_user.py": {
        "REQUIRE_AUTHENTICATION": "true",
        "ENABLE_BACKEND_ACCESS_CONTROL": "true",
    },
}

PER_FILE_TIMEOUT = 300


def _error_case(classname, name, message):
    case = ET.Element("testcase", {"classname": classname, "name": name})
    error = ET.SubElement(case, "error", {"message": message[:400]})
    error.text = message
    return case


def run_module(path, env, workdir):
    stem = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(workdir, stem + ".xml")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        path,
        "-q",
        "-p",
        "no:cacheprovider",
        "--junitxml=" + out,
        "--confcutdir=" + os.path.dirname(os.path.abspath(path)),
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=os.environ.get("SUITE_WORKDIR", "/workspace"),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=PER_FILE_TIMEOUT,
        )
        output = proc.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b"").decode("utf-8", "replace")
        return [_error_case(stem, "module", "timed out after %ss\n%s" % (PER_FILE_TIMEOUT, output[-3000:]))]

    if not os.path.isfile(out):
        return [_error_case(stem, "module", "module produced no result\n" + output[-3000:])]

    try:
        tree = ET.parse(out)
    except ET.ParseError as exc:
        return [_error_case(stem, "module", "unreadable result: %s\n%s" % (exc, output[-3000:]))]

    cases = list(tree.iter("testcase"))
    if not cases:
        return [_error_case(stem, "module", "no tests ran\n" + output[-3000:])]
    return cases


def main():
    if len(sys.argv) != 3:
        print("usage: run_junit.py <suite-dir> <out-xml>", file=sys.stderr)
        return 2
    suite_dir = os.path.abspath(sys.argv[1])
    out_path = os.path.abspath(sys.argv[2])
    suite_name = os.path.basename(suite_dir.rstrip("/"))

    files = sorted(
        os.path.join(suite_dir, name)
        for name in os.listdir(suite_dir)
        if name.startswith("test_") and name.endswith(".py")
    )
    if not files:
        files = []

    tmp_root = os.environ.get("TMPDIR") or "/tmp"
    workdir = tempfile.mkdtemp(prefix="cognee-%s-" % suite_name, dir=tmp_root)

    merged = []
    for path in files:
        name = os.path.basename(path)
        env = dict(os.environ)
        env.update(BASE_ENV)
        env.update(FILE_ENV.get(name, {}))
        state = os.path.join(workdir, os.path.splitext(name)[0])
        for sub in ("system", "data", "logs"):
            os.makedirs(os.path.join(state, sub), exist_ok=True)
        env["SYSTEM_ROOT_DIRECTORY"] = os.path.join(state, "system")
        env["DATA_ROOT_DIRECTORY"] = os.path.join(state, "data")
        env["COGNEE_LOGS_DIR"] = os.path.join(state, "logs")
        env["HOME"] = state
        merged.extend(run_module(path, env, workdir))

    suite = ET.Element("testsuite", {"name": suite_name, "tests": str(len(merged))})
    for case in merged:
        suite.append(case)
    root = ET.Element("testsuites")
    root.append(suite)

    directory = os.path.dirname(out_path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
    shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
