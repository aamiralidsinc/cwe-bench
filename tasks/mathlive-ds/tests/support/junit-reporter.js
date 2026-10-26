'use strict';
/**
 * Minimal JUnit XML reporter. The hidden suites each run in their own jest process;
 * the output file is chosen with the JUNIT_OUT environment variable. Kept dependency
 * free so the verifier needs nothing beyond the project's own tree.
 */
const fs = require('fs');
const path = require('path');

function esc(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

class JUnitReporter {
  constructor(globalConfig, options) {
    this.options = options || {};
  }

  onRunComplete(_contexts, results) {
    const out =
      this.options.outputFile ||
      process.env.JUNIT_OUT ||
      path.join(process.cwd(), 'results.xml');
    const cases = [];
    let failures = 0;
    let errors = 0;
    let skipped = 0;
    for (const suite of results.testResults || []) {
      const file = path.basename(suite.testFilePath || suite.testFile || '');
      for (const assertion of suite.testResults || suite.assertionResults || []) {
        const name = [...(assertion.ancestorTitles || []), assertion.title].join(' > ');
        let body = '';
        if (assertion.status === 'failed') {
          const message = (assertion.failureMessages || []).join('\n');
          const first = String(message).split('\n')[0];
          body = `<failure message="${esc(first)}">${esc(message)}</failure>`;
          failures += 1;
        } else if (assertion.status === 'pending' || assertion.status === 'todo') {
          body = '<skipped/>';
          skipped += 1;
        }
        cases.push(
          `<testcase classname="${esc(file)}" name="${esc(name)}">${body}</testcase>`
        );
      }
      const assertions = suite.testResults || suite.assertionResults || [];
      if (suite.failureMessage && assertions.length === 0) {
        const message = suite.failureMessage;
        cases.push(
          `<testcase classname="${esc(file)}" name="suite"><error message="${esc(
            String(message).split('\n')[0]
          )}">${esc(message)}</error></testcase>`
        );
        errors += 1;
      }
    }
    const xml =
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      `<testsuites><testsuite name="hidden" tests="${cases.length}" failures="${failures}" ` +
      `errors="${errors}" skipped="${skipped}">${cases.join('')}</testsuite></testsuites>\n`;
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, xml);
  }
}

module.exports = JUnitReporter;
