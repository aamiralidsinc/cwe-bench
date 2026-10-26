#!/usr/bin/env node
'use strict';

// Turns jest's --json report into the JUnit XML the scorer reads.
const fs = require('fs');
const path = require('path');

const [, , jsonPath, out] = process.argv;

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

const results = [];

try {
  const report = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  for (const suite of report.testResults || []) {
    for (const assertion of suite.assertionResults || []) {
      if (assertion.status === 'pending' || assertion.status === 'todo') {
        continue;
      }
      results.push({
        classname: 'project/' + (assertion.ancestorTitles || []).join(' '),
        name: assertion.title,
        ok: assertion.status === 'passed',
        message: (assertion.failureMessages || []).join('\n'),
      });
    }
  }
} catch (e) {
  results.push({
    classname: 'project/harness',
    name: 'the project suite ran',
    ok: false,
    message: `could not read the jest report: ${e && e.message}`,
  });
}

if (!results.length) {
  results.push({
    classname: 'project/harness',
    name: 'the project suite ran',
    ok: false,
    message: 'the project suite produced no results',
  });
}

const failures = results.filter((r) => !r.ok).length;
const lines = [
  '<?xml version="1.0" encoding="UTF-8"?>',
  `<testsuite name="project" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`,
];
for (const r of results) {
  if (r.ok) {
    lines.push(`  <testcase classname="project/${esc((r.classname || '').replace(/^project\//, ''))}" name="${esc(r.name)}"/>`);
  } else {
    lines.push(`  <testcase classname="project/${esc((r.classname || '').replace(/^project\//, ''))}" name="${esc(r.name)}">`);
    lines.push(`    <failure message="${esc(r.message).slice(0, 500)}">${esc(r.message).slice(0, 4000)}</failure>`);
    lines.push('  </testcase>');
  }
}
lines.push('</testsuite>', '');
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, lines.join('\n'));
