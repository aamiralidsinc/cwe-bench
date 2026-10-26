#!/usr/bin/env python3
"""Merge several JUnit XML files into one, preserving every testcase element."""
import sys
import xml.etree.ElementTree as ET

out, paths = sys.argv[1], sys.argv[2:]
suite = ET.Element('testsuite', name='Mocha Tests')
count = 0
for path in paths:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        continue
    for case in root.iter('testcase'):
        suite.append(case)
        count += 1
if count == 0:
    sys.exit('no testcases found in the input XML files')
suite.set('tests', str(count))
ET.ElementTree(suite).write(out, encoding='UTF-8', xml_declaration=True)
