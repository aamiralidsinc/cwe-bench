#!/usr/bin/env python3
"""Run every PHP test script in one directory and write a JUnit XML report.

usage: run_tests.py <directory> <junit-xml-out> <per-test-timeout-seconds>

Each script exits 0 when it passes and non-zero with a message on stderr when it fails.
A script that does not finish within the timeout is recorded as a failure: for the
conversion tests that is exactly the denial-of-service condition they are looking for.
"""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    directory, out, timeout = sys.argv[1], sys.argv[2], float(sys.argv[3])
    directory = os.path.abspath(directory)
    group = os.path.basename(directory.rstrip('/'))

    suite = ET.Element('testsuite', name=group)
    files = sorted(f for f in os.listdir(directory) if f.endswith('.php'))
    failures = 0

    for filename in files:
        name = filename[:-4]
        case = ET.SubElement(suite, 'testcase', classname=f'{group}.{name}', name=name)
        try:
            proc = subprocess.run(
                ['php', os.path.join(directory, filename)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
            )
            if proc.returncode != 0:
                failures += 1
                failure = ET.SubElement(case, 'failure', message=f'exit {proc.returncode}')
                failure.text = (proc.stdout + proc.stderr).decode('utf-8', 'replace')[-6000:]
        except subprocess.TimeoutExpired:
            failures += 1
            failure = ET.SubElement(case, 'failure', message='time limit exceeded')
            failure.text = f'conversion did not finish within {timeout}s'

    suite.set('tests', str(len(files)))
    suite.set('failures', str(failures))
    suite.set('errors', '0')
    suite.set('skipped', '0')
    ET.ElementTree(suite).write(out, encoding='utf-8', xml_declaration=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
