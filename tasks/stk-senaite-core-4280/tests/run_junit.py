# -*- coding: utf-8 -*-
"""Run one hidden suite and write JUnit XML (Python 2.7 compatible)."""

import os
import sys
import traceback
import unittest
from xml.sax.saxutils import escape


class XmlResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        unittest.TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.records = []

    def _record(self, test, status, err=None):
        classname = "%s.%s" % (test.__class__.__module__,
                               test.__class__.__name__)
        name = getattr(test, "_testMethodName", str(test))
        detail = ""
        message = ""
        if err is not None:
            message = "%s: %s" % (err[0].__name__, err[1])
            detail = "".join(traceback.format_exception(*err))
        self.records.append((classname, name, status, message, detail))

    def addSuccess(self, test):
        unittest.TextTestResult.addSuccess(self, test)
        self._record(test, "pass")

    def addFailure(self, test, err):
        unittest.TextTestResult.addFailure(self, test, err)
        self._record(test, "fail", err)

    def addError(self, test, err):
        unittest.TextTestResult.addError(self, test, err)
        self._record(test, "error", err)

    def addSkip(self, test, reason):
        unittest.TextTestResult.addSkip(self, test, reason)
        self._record(test, "skipped", (Exception, reason, None))


def write_xml(records, path, suite_name):
    failures = sum(1 for r in records if r[2] == "fail")
    errors = sum(1 for r in records if r[2] == "error")
    skipped = sum(1 for r in records if r[2] == "skipped")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<testsuites>",
             '<testsuite name="%s" tests="%d" failures="%d" errors="%d" skipped="%d">'
             % (escape(suite_name), len(records), failures, errors, skipped)]
    for classname, name, status, message, detail in records:
        attrs = 'classname="%s" name="%s"' % (escape(classname), escape(name))
        if status == "pass":
            lines.append("<testcase %s/>" % attrs)
        elif status == "skipped":
            lines.append('<testcase %s><skipped message="%s"/></testcase>'
                         % (attrs, escape(message)))
        else:
            tag = "failure" if status == "fail" else "error"
            lines.append('<testcase %s><%s message="%s">%s</%s></testcase>'
                         % (attrs, tag, escape(message), escape(detail), tag))
    lines.append("</testsuite>")
    lines.append("</testsuites>")
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    handle = open(path, "w")
    try:
        handle.write("\n".join(lines) + "\n")
    finally:
        handle.close()


def main():
    test_dir = os.path.abspath(sys.argv[1])
    out_path = os.path.abspath(sys.argv[2])
    suite_name = os.path.basename(test_dir.rstrip("/"))

    here = os.path.dirname(os.path.abspath(__file__))
    for entry in (os.path.join(here, "harness"), here, "/workspace/src"):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    loader = unittest.TestLoader()
    try:
        suite = loader.discover(test_dir, pattern="test_*.py",
                                top_level_dir=test_dir)
    except Exception:
        suite = unittest.TestSuite()

    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2,
                                     resultclass=XmlResult)
    result = runner.run(suite)
    records = getattr(result, "records", [])
    if not records:
        records = [("runner", "no_tests", "error",
                    "no tests were discovered in %s" % test_dir, "")]
    write_xml(records, out_path, suite_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
