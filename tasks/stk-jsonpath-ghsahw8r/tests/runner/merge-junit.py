#!/usr/bin/env python3
"""Merge the node-test and mocha JUnit files into one <testsuites> document.

Usage: merge-junit.py <a.xml> <b.xml> <out.xml>
A missing or unparseable input contributes nothing; the output is always written.
"""
import sys
import xml.etree.ElementTree as ET


def main():
    inputs, out = sys.argv[1:-1], sys.argv[-1]
    root = ET.Element("testsuites")
    for path in inputs:
        try:
            child = ET.parse(path).getroot()
        except (OSError, ET.ParseError):
            continue
        if child.tag == "testsuites":
            for case in list(child):
                root.append(case)
        else:
            root.append(child)
    ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
