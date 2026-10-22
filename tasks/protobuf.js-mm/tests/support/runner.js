'use strict';
// Shared harness for the hidden protobuf.js tests.
//
// Every test drives a real public entry point of the library in /app. A test is
// a { name, run } pair; run() throws to fail. Results are written as JUnit XML
// so score.py can read them. No product code computes expectations: assertions
// are plain checks on the value the library handed back.

const fs = require('fs');
const path = require('path');

function xmlEscape(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]),
  );
}

function runSuite(suiteName, cases, outFile) {
  const results = [];
  for (const c of cases) {
    const start = Date.now();
    let failure = null;
    try {
      c.run();
    } catch (e) {
      failure = e && e.stack ? e.stack : String(e);
    }
    results.push({ name: c.name, time: (Date.now() - start) / 1000, failure });
    const tag = failure ? 'FAIL' : 'ok';
    process.stdout.write(`[${tag}] ${suiteName} :: ${c.name}\n`);
    if (failure) process.stdout.write('    ' + String(failure).split('\n')[0] + '\n');
  }
  const fails = results.filter((r) => r.failure).length;
  const body = results
    .map((r) => {
      const open = `  <testcase classname="${xmlEscape(suiteName)}" name="${xmlEscape(r.name)}" time="${r.time}">`;
      if (!r.failure) return open + '</testcase>';
      return (
        open +
        `\n    <failure message="assertion failed">${xmlEscape(r.failure)}</failure>\n  </testcase>`
      );
    })
    .join('\n');
  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<testsuite name="${xmlEscape(suiteName)}" tests="${results.length}" failures="${fails}">\n` +
    body +
    `\n</testsuite>\n`;
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, xml);
  process.stdout.write(`${suiteName}: ${results.length - fails}/${results.length} passed -> ${outFile}\n`);
  return fails;
}

module.exports = { runSuite };
