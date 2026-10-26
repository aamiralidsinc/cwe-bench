#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Loads the submitted library through its public entry point, runs every case in the group and
 * writes a JUnit XML file the scorer reads. A case passes when its promise resolves and fails
 * when it throws. Setup, expected values and clean-up are plain Node/child-process code in the
 * case tables; no product helper is used to decide an outcome.
 */

const fs = require('fs');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const PRODUCT = process.env.PRODUCT_ENTRY || '/workspace/simple-git/dist/cjs/index.js';
const CASE_TIMEOUT_MS = 120000;

function esc(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function writeXml(results) {
  const failures = results.filter((r) => !r.ok).length;
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<testsuite name="${esc(GROUP)}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`,
  ];
  for (const result of results) {
    if (result.ok) {
      lines.push(`  <testcase classname="${esc(result.classname)}" name="${esc(result.name)}"/>`);
    } else {
      const message = result.message || 'failed';
      lines.push(`  <testcase classname="${esc(result.classname)}" name="${esc(result.name)}">`);
      lines.push(`    <failure message="${esc(message).slice(0, 500)}">${esc(message).slice(0, 4000)}</failure>`);
      lines.push('  </testcase>');
    }
  }
  lines.push('</testsuite>', '');
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, lines.join('\n'));
}

function withTimeout(promise, name) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${name} did not finish within ${CASE_TIMEOUT_MS}ms`)), CASE_TIMEOUT_MS);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

async function main() {
  const results = [];
  let lib;

  try {
    lib = require(PRODUCT);
    if (typeof lib.simpleGit !== 'function') {
      throw new Error('the product did not expose its factory');
    }
  } catch (e) {
    results.push({
      classname: 'harness',
      name: 'product entry point loads',
      ok: false,
      message: `could not load ${PRODUCT}: ${e && (e.stack || e.message)}`,
    });
    writeXml(results);
    return;
  }

  const suitePath = path.join(__dirname, '..', GROUP, 'cases.js');
  let suite;

  try {
    suite = require(suitePath)(lib);
  } catch (e) {
    results.push({
      classname: 'harness',
      name: `suite loads: ${GROUP}`,
      ok: false,
      message: `suite error: ${e && (e.stack || e.message)}`,
    });
    writeXml(results);
    return;
  }

  for (const entry of suite) {
    try {
      await withTimeout(Promise.resolve().then(entry.run), entry.name);
      results.push({ classname: entry.classname, name: entry.name, ok: true });
    } catch (e) {
      results.push({
        classname: entry.classname,
        name: entry.name,
        ok: false,
        message: (e && (e.stack || e.message)) || String(e),
      });
    }
  }

  writeXml(results);
}

main().catch((e) => {
  try {
    writeXml([
      { classname: 'harness', name: 'runner', ok: false, message: String(e && (e.stack || e.message)) },
    ]);
  } catch (_) {
    process.exitCode = 1;
  }
});
