#!/usr/bin/env python3
"""Convert `go test -json` output into a JUnit XML file.

    gojson2junit.py <go-test-json-file> <suitename>  > results.xml

Reads the JSON event stream produced by `go test -json` (lines that do not
parse as JSON, e.g. compiler errors on stderr, are tolerated), and writes one
<testcase> per Go test with a <failure> child for any test that did not pass.

If no test results are found at all (for example the package failed to build
or panicked in TestMain before any test ran), a single failing synthetic
testcase is emitted so the group is scored as failed rather than silently
empty.
"""
import json
import sys
import xml.etree.ElementTree as ET


def main():
    src, suite = sys.argv[1], sys.argv[2]
    results = {}  # test name -> "pass"|"fail"|"skip"
    outputs = {}  # test name -> accumulated output
    raw = []
    with open(src, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                raw.append(line)
                continue
            action = ev.get("Action", "")
            test = ev.get("Test", "")
            if action == "output":
                key = test or "__package__"
                outputs.setdefault(key, []).append(ev.get("Output", ""))
                continue
            if not test:
                # package-level pass/fail/skip - ignore, per-test wins
                continue
            if action in ("pass", "fail", "skip"):
                results[test] = action

    suite_el = ET.Element("testsuite", {"name": suite})
    nfail = 0
    for test in sorted(results):
        res = results[test]
        tc = ET.SubElement(suite_el, "testcase", {"classname": suite, "name": test})
        if res == "fail":
            nfail += 1
            msg = "".join(outputs.get(test, []))[:4000]
            ET.SubElement(tc, "failure", {"message": "test failed"}).text = msg
        elif res == "skip":
            ET.SubElement(tc, "skipped")

    if not results:
        # Nothing ran - emit a synthetic failure carrying whatever we captured.
        tc = ET.SubElement(suite_el, "testcase",
                           {"classname": suite, "name": "SETUP_OR_BUILD"})
        detail = "".join(outputs.get("__package__", [])) + "\n" + "\n".join(raw)
        ET.SubElement(tc, "failure", {"message": "no tests ran"}).text = detail[:4000]
        nfail = 1

    total = len(results) if results else 1
    suite_el.set("tests", str(total))
    suite_el.set("failures", str(nfail))
    sys.stdout.write(ET.tostring(suite_el, encoding="unicode"))


if __name__ == "__main__":
    main()
