#!/usr/bin/env python3
"""Convert `go test -json` output into a JUnit XML file for the verifier.

Usage: gotest_junit.py <group> <input.json> <output.xml>
"""
import json
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    group, source, destination = sys.argv[1], sys.argv[2], sys.argv[3]
    outcomes = {}
    with open(source, errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = event.get("Test")
            action = event.get("Action")
            if not name or action not in ("pass", "fail", "skip"):
                continue
            package = event.get("Package") or group
            outcomes[(package, name)] = action

    suite = ET.Element("testsuite", name=group, tests=str(len(outcomes)))
    for (package, name), action in sorted(outcomes.items()):
        case = ET.SubElement(suite, "testcase", classname=package, name=name)
        if action == "fail":
            ET.SubElement(case, "failure", message="test failed")
        elif action == "skip":
            ET.SubElement(case, "skipped")
    ET.ElementTree(suite).write(destination, encoding="utf-8", xml_declaration=True)
    print(f"{group}: {len(outcomes)} tests -> {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
