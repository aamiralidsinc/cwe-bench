#!/usr/bin/env python3
"""Merge the surefire report files of one hidden group into a single JUnit XML file.

A group that produced no test cases (compilation or start-up failure) becomes one failing
test case, so a broken run is a failing group rather than a missing result.
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET


def tail(path, n=40):
    try:
        with open(path, errors="replace") as fh:
            return "".join(fh.readlines()[-n:])
    except OSError:
        return ""


def main():
    reports, out, group, rc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    cases = []
    for path in sorted(glob.glob(os.path.join(reports, "TEST-*.xml"))):
        try:
            root = ET.parse(path).getroot()
        except Exception:
            continue
        for case in root.iter("testcase"):
            cases.append(case)

    suite = ET.Element("testsuite", name="hidden-" + group)
    failures = errors = skipped = 0
    if not cases:
        case = ET.SubElement(suite, "testcase", classname="verifier." + group, name="group")
        message = "the %s group produced no test results (mvn exit %s)" % (group, rc)
        failure = ET.SubElement(case, "failure", message=message)
        failure.text = tail("/workspace/.htests/mvn-%s.log" % group)
        failures = 1
    else:
        for source in cases:
            case = ET.SubElement(
                suite,
                "testcase",
                classname=source.get("classname", ""),
                name=source.get("name", ""),
            )
            if source.get("time"):
                case.set("time", source.get("time"))
            for tag in ("failure", "error", "skipped"):
                for bad in source.findall(tag):
                    made = ET.SubElement(case, tag, dict(bad.attrib))
                    made.text = bad.text
                    if tag == "failure":
                        failures += 1
                    elif tag == "error":
                        errors += 1
                    else:
                        skipped += 1
    suite.set("tests", str(len(suite.findall("testcase"))))
    suite.set("failures", str(failures))
    suite.set("errors", str(errors))
    suite.set("skipped", str(skipped))
    parent = os.path.dirname(out)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    ET.ElementTree(suite).write(out, encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    main()
