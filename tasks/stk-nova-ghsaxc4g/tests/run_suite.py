#!/usr/bin/env python2
"""Run one hidden group with the standard library and write JUnit XML.

Usage: run_suite.py <test-directory> <junit-xml-path> [suite-name]
"""
import os
import sys
import time
import traceback
import unittest
import xml.sax.saxutils as saxutils


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for test in flatten(item):
                yield test
        else:
            yield item


def split_id(test):
    ident = test.id()
    if '.' in ident:
        classname, name = ident.rsplit('.', 1)
    else:
        classname, name = 'tests', ident
    return classname, name


def write_xml(out, suite_name, cases, elapsed):
    failures = sum(1 for c in cases if c['status'] in ('fail', 'error'))
    skipped = sum(1 for c in cases if c['status'] == 'skip')
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<testsuites>',
             '  <testsuite name="%s" tests="%d" failures="%d" errors="%d" '
             'skipped="%d" time="%.3f">' %
             (saxutils.escape(suite_name), len(cases), failures, 0, skipped,
              elapsed)]
    for case in cases:
        parts.append('    <testcase classname="%s" name="%s" time="0">' %
                     (saxutils.escape(case['classname']),
                      saxutils.escape(case['name'])))
        if case['status'] == 'fail':
            parts.append('      <failure message="%s">%s</failure>' %
                         (saxutils.escape(case['message'][:500]),
                          saxutils.escape(case['detail'])))
        elif case['status'] == 'error':
            parts.append('      <error message="%s">%s</error>' %
                         (saxutils.escape(case['message'][:500]),
                          saxutils.escape(case['detail'])))
        elif case['status'] == 'skip':
            parts.append('      <skipped message="%s"/>' %
                         saxutils.escape(case['message'][:500]))
        parts.append('    </testcase>')
    parts.append('  </testsuite>')
    parts.append('</testsuites>')
    f = open(out, 'wb')
    try:
        f.write('\n'.join(parts))
    finally:
        f.close()


def main(argv):
    if len(argv) < 3:
        print('usage: run_suite.py <dir> <out.xml> [name]')
        return 2
    directory, out = argv[1], argv[2]
    suite_name = argv[3] if len(argv) > 3 else os.path.basename(
        directory.rstrip('/'))
    root = os.path.dirname(os.path.abspath(directory))
    sys.path.insert(0, root)

    cases = []
    started = time.time()
    try:
        suite = unittest.TestLoader().discover(
            directory, pattern='test_*.py', top_level_dir=root)
        tests = list(flatten(suite))
        result = unittest.TestResult()
        suite.run(result)
    except Exception:
        detail = traceback.format_exc()
        cases.append({'classname': suite_name, 'name': 'collection',
                      'status': 'error',
                      'message': detail.splitlines()[-1] if detail else
                      'collection failed', 'detail': detail})
        write_xml(out, suite_name, cases, time.time() - started)
        return 1

    failed = {}
    for test, detail in result.failures:
        failed[test.id()] = ('fail', detail)
    for test, detail in result.errors:
        failed[test.id()] = ('error', detail)
    skipped = {}
    for test, reason in result.skipped:
        skipped[test.id()] = reason

    for test in tests:
        classname, name = split_id(test)
        ident = test.id()
        if ident in failed:
            status, detail = failed[ident]
            message = detail.strip().splitlines()[-1] if detail.strip() else \
                status
            cases.append({'classname': classname, 'name': name,
                          'status': status, 'message': message,
                          'detail': detail})
        elif ident in skipped:
            cases.append({'classname': classname, 'name': name,
                          'status': 'skip', 'message': skipped[ident],
                          'detail': ''})
        else:
            cases.append({'classname': classname, 'name': name,
                          'status': 'pass', 'message': '', 'detail': ''})

    write_xml(out, suite_name, cases, time.time() - started)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
