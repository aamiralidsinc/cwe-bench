#!/usr/bin/env python3
"""Merge the JUnit XML written by each module into one testsuite for score.py.

Usage: merge_junit.py <out.xml> <report-dir>... <group>

Always writes a file: when a module produced no results (compile error, crash, missing suite)
a single failing testcase is recorded so the reward is 0 instead of the group looking missing.
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    out = sys.argv[1]
    dirs = sys.argv[2:-1]
    group = sys.argv[-1]
    root = ET.Element("testsuite", name="hidden-" + group)
    count = 0
    for directory in dirs:
        for path in sorted(glob.glob(os.path.join(directory, "*.xml"))):
            try:
                tree = ET.parse(path)
            except Exception:
                continue
            for case in tree.iter("testcase"):
                root.append(case)
                count += 1
    if count == 0:
        case = ET.SubElement(root, "testcase", classname="hidden." + group, name="suite_did_not_run")
        failure = ET.SubElement(case, "failure")
        failure.text = "the " + group + " suite produced no JUnit results"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
