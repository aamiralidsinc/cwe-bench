'use strict';
// Minimal JUnit reporter: jest calls onRunComplete with every test outcome, and this writes the
// XML the verifier's score.py reads. The output path comes from JUNIT_OUT so the orchestrator can
// keep the report inside the agent-writable staging directory.
const fs = require('fs');
const path = require('path');

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

class JunitReporter {
  constructor() {
    this.out = process.env.JUNIT_OUT;
  }

  onRunComplete(_contexts, results) {
    if (!this.out) return;

    const cases = [];
    for (const suite of results.testResults || []) {
      const classname = suite.testFilePath || 'unknown';
      const assertions = suite.testResults || [];
      if (assertions.length === 0) {
        const message =
          suite.failureMessage ||
          (suite.testExecError && suite.testExecError.message) ||
          'test suite did not run';
        cases.push({ classname, name: 'suite', failure: message, skipped: false });
        continue;
      }
      for (const assertion of assertions) {
        cases.push({
          classname,
          name: assertion.fullName || assertion.title || 'test',
          failure: assertion.status === 'failed' ? (assertion.failureMessages || []).join('\n') : '',
          skipped: assertion.status === 'pending' || assertion.status === 'todo',
        });
      }
    }

    const failures = cases.filter((entry) => entry.failure).length;
    const skipped = cases.filter((entry) => entry.skipped).length;
    const body = cases
      .map((entry) => {
        const attrs = `classname="${escapeXml(entry.classname)}" name="${escapeXml(entry.name)}"`;
        if (entry.failure) {
          return `    <testcase ${attrs}><failure message="failed">${escapeXml(entry.failure)}</failure></testcase>`;
        }
        if (entry.skipped) return `    <testcase ${attrs}><skipped/></testcase>`;
        return `    <testcase ${attrs}/>`;
      })
      .join('\n');

    const xml =
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      `<testsuites tests="${cases.length}" failures="${failures}" skipped="${skipped}">\n` +
      `  <testsuite name="jest" tests="${cases.length}" failures="${failures}" skipped="${skipped}">\n` +
      `${body}\n` +
      '  </testsuite>\n' +
      '</testsuites>\n';

    fs.mkdirSync(path.dirname(this.out), { recursive: true });
    fs.writeFileSync(this.out, xml);
  }
}

module.exports = JunitReporter;
