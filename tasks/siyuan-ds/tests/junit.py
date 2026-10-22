#!/usr/bin/env python3
"""Convert a `go test -json` stream into a JUnit XML file.

Every test event becomes one testcase. A stream that produced no test at all
(for example because the package did not compile) becomes a single failing
testcase, so a broken runner can never look like a pass.
"""
import json
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: junit.py <output.xml>", file=sys.stderr)
        return 2
    out_path = sys.argv[1]

    cases = {}
    package_output = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        package = event.get("Package", "")
        test = event.get("Test")
        action = event.get("Action")
        output = event.get("Output", "")
        if test:
            case = cases.setdefault((package, test), {"output": [], "action": None})
            if action in ("pass", "fail", "skip"):
                case["action"] = action
            if output:
                case["output"].append(output)
        else:
            if output:
                package_output.setdefault(package, []).append(output)

    suite = ET.Element("testsuite", name=out_path)
    count = 0
    for (package, test), case in sorted(cases.items()):
        count += 1
        testcase = ET.SubElement(suite, "testcase", classname=package, name=test)
        text = "".join(case["output"])
        if case["action"] == "fail":
            failure = ET.SubElement(testcase, "failure")
            failure.text = text
        elif case["action"] == "skip":
            ET.SubElement(testcase, "skipped")
        elif case["action"] is None:
            failure = ET.SubElement(testcase, "failure")
            failure.text = "test did not finish\n" + text

    if count == 0:
        testcase = ET.SubElement(suite, "testcase", classname="runner", name="no-tests")
        failure = ET.SubElement(testcase, "failure")
        failure.text = "no tests were produced\n" + "".join(
            line for lines in package_output.values() for line in lines
        )
        count = 1

    suite.set("tests", str(count))
    ET.ElementTree(suite).write(out_path, encoding="utf-8", xml_declaration=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
