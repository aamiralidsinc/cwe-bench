#!/usr/bin/env python3
"""Make the project's own JUnit file safe to merge with the hidden suites.

Node's built-in JUnit reporter emits one <testsuite> per describe block but writes every
<testcase> with classname="test", so same-named tests from different blocks collide after
scoring. Rewrite each testcase's classname to include its suite name. If the file is missing
(the project's tests could not be run at all), write a single failing case so the run scores as
a functional failure instead of a verifier error.

Usage: fix_junit.py <project.xml>
"""
import os
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1]


def write_failure(message):
    root = ET.Element("testsuite", name="project", tests="1", failures="1")
    case = ET.SubElement(root, "testcase", classname="functional/project", name="project tests run")
    failure = ET.SubElement(case, "failure", message=message[:500])
    failure.text = message
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


if not os.path.isfile(path) or os.path.getsize(path) == 0:
    write_failure("the project's own tests produced no results")
    sys.exit(0)

try:
    tree = ET.parse(path)
except ET.ParseError as e:
    write_failure(f"the project's own test results could not be read: {e}")
    sys.exit(0)

root = tree.getroot()
for suite in root.iter("testsuite"):
    suite_name = suite.get("name", "project")
    for case in suite.findall("testcase"):
        case.set("classname", "functional/project/" + suite_name)

tree.write(path, encoding="utf-8", xml_declaration=True)
