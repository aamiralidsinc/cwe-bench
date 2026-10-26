#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Each case opens the application through its real entry point in a fresh jsdom page and either
 * throws (failure) or returns normally (pass). The runner writes the JUnit XML the scorer reads.
 */

const fs = require('fs');
const path = require('path');
const harness = require('./harness');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const CASE_TIMEOUT_MS = 45000;

function esc(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function writeXml(results) {
  const failures = results.filter(result => !result.ok).length;
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<testsuite name="${esc(GROUP)}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`
  ];
  for (const result of results) {
    if (result.ok) {
      lines.push(`  <testcase classname="${esc(result.classname)}" name="${esc(result.name)}"/>`);
    } else {
      const message = result.message || 'failed';
      lines.push(`  <testcase classname="${esc(result.classname)}" name="${esc(result.name)}">`);
      lines.push(`    <failure message="${esc(message).slice(0, 500)}">${esc(message).slice(0, 8000)}</failure>`);
      lines.push('  </testcase>');
    }
  }
  lines.push('</testsuite>', '');
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, lines.join('\n'));
}

function withTimeout(promise, testName) {
  let timer;
  const timeout = new Promise((resolve, reject) => {
    timer = setTimeout(
      () => reject(new Error(`case timed out after ${CASE_TIMEOUT_MS / 1000}s: ${testName}`)),
      CASE_TIMEOUT_MS
    );
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

async function main() {
  const results = [];
  let entries;
  try {
    const modulePath = path.join(__dirname, '..', GROUP, 'cases.js');
    entries = require(modulePath)(harness);
  } catch (err) {
    writeXml([{
      classname: 'harness',
      name: 'suite loads',
      ok: false,
      message: `suite error: ${err && (err.stack || err.message || err)}`
    }]);
    process.exit(0);
  }

  for (const entry of entries) {
    try {
      await withTimeout(Promise.resolve().then(() => entry.run()), entry.name);
      results.push({ classname: GROUP, name: entry.name, ok: true });
    } catch (err) {
      results.push({
        classname: GROUP,
        name: entry.name,
        ok: false,
        message: (err && (err.message || err.stack)) || String(err)
      });
    }
  }

  writeXml(results);
}

main().then(
  () => process.exit(0),
  err => {
    try {
      writeXml([{
        classname: 'harness',
        name: 'runner',
        ok: false,
        message: `runner error: ${err && (err.stack || err.message || err)}`
      }]);
    } catch (ignored) {
      // nothing else to do
    }
    process.exit(0);
  }
);
