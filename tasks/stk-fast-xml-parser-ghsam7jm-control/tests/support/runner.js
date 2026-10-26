#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Loads the library through its public entry point, runs every case in the group, and writes a
 * JUnit XML file the scorer reads. A case either throws (failure) or returns normally (pass).
 * Expected values are literals in the case tables; no product code is used to compute them.
 *
 * The functional group also runs a pristine copy of the project's own entity specification with
 * the project's native runner (Jasmine), staged at /workspace/spec/entities_spec.js by test.sh.
 */

const fs = require('fs');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const PRODUCT = process.env.PRODUCT_ENTRY || '/workspace/src/fxp.js';
const PROJECT_SPEC = process.env.PROJECT_SPEC || '/workspace/spec/entities_spec.js';

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function writeXml(results) {
  const failures = results.filter(r => !r.ok).length;
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<testsuite name="${esc(GROUP)}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`,
  ];
  for (const r of results) {
    if (r.ok) {
      lines.push(`  <testcase classname="${esc(r.classname)}" name="${esc(r.name)}"/>`);
    } else {
      const msg = r.message || 'failed';
      lines.push(`  <testcase classname="${esc(r.classname)}" name="${esc(r.name)}">`);
      lines.push(`    <failure message="${esc(msg).slice(0, 500)}">${esc(msg).slice(0, 4000)}</failure>`);
      lines.push('  </testcase>');
    }
  }
  lines.push('</testsuite>', '');
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, lines.join('\n'));
}

async function runProjectSpec() {
  let Jasmine;
  try {
    Jasmine = require('jasmine');
  } catch (e) {
    return [{
      classname: 'functional/project', name: 'project entity specification',
      ok: false, message: `the project runner is unavailable: ${e && e.message}`,
    }];
  }
  const results = [];
  let runner;
  try {
    runner = new Jasmine({ projectBaseDir: '/workspace' });
    runner.clearReporters();
    runner.addReporter({
      specDone(r) {
        results.push({
          classname: 'functional/project',
          name: r.fullName,
          ok: r.status === 'passed',
          message: (r.failedExpectations || []).map(f => f.message).join(' | '),
        });
      },
    });
    runner.addSpecFile(PROJECT_SPEC);
    runner.exitOnCompletion = false;
    await runner.execute();
  } catch (e) {
    return [{
      classname: 'functional/project', name: 'project entity specification',
      ok: false, message: `the project specification did not run: ${e && (e.stack || e.message)}`,
    }];
  }
  return results;
}

async function main() {
  const results = [];
  let XMLParser;
  try {
    const product = require(PRODUCT);
    XMLParser = product.XMLParser;
    if (typeof XMLParser !== 'function') {
      throw new Error('the library did not expose its parser');
    }
  } catch (e) {
    results.push({
      classname: 'harness', name: 'product entry point loads',
      ok: false, message: `could not load ${PRODUCT}: ${e && e.message}`,
    });
    writeXml(results);
    return;
  }

  const modulePath = GROUP === 'functional'
    ? path.join(__dirname, '..', 'functional', 'cases.js')
    : path.join(__dirname, '..', 'security', 'cases.js');

  let entries = [];
  try {
    entries = require(modulePath)(XMLParser);
  } catch (e) {
    results.push({
      classname: 'harness', name: `suite loads: ${path.basename(modulePath)}`,
      ok: false, message: `suite error: ${e && (e.stack || e.message)}`,
    });
  }

  for (const entry of entries) {
    try {
      entry.run();
      results.push({ classname: entry.classname, name: entry.name, ok: true });
    } catch (e) {
      results.push({
        classname: entry.classname, name: entry.name,
        ok: false, message: (e && e.message) || String(e),
      });
    }
  }

  if (GROUP === 'functional') {
    results.push(...await runProjectSpec());
  }

  writeXml(results);
}

main().catch(e => {
  try {
    writeXml([{ classname: 'harness', name: 'runner', ok: false, message: String(e && (e.stack || e.message)) }]);
  } catch (_) {
    process.exitCode = 1;
  }
});
