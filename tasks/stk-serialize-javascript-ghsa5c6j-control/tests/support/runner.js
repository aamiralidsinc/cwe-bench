#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Loads the submitted library through its package entry point, runs every case in the group, and
 * writes JUnit XML for the scorer. A case either throws (failure) or returns normally (pass).
 * Expected values are literals in the case tables; no product code computes them. The functional
 * group also runs a pristine copy of the project's own unit suite through a minimal
 * describe/it/beforeEach harness, so the library's documented behaviour is exercised too.
 */

const fs = require('fs');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const PRODUCT = process.env.PRODUCT_ENTRY || '/workspace';

function esc(s) {
  return String(s)
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uFFFE\uFFFF]/g, '')
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
      lines.push(`    <failure message="${esc(msg.slice(0, 500))}">${esc(msg.slice(0, 4000))}</failure>`);
      lines.push('  </testcase>');
    }
  }
  lines.push('</testsuite>', '');
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, lines.join('\n'));
}

// Run the project's own unit file (a pristine copy shipped with the hidden tests) through a
// minimal describe/it/beforeEach harness. chai resolves from NODE_PATH.
function runProjectSuite(results) {
  const frames = [{ befores: [] }];
  global.describe = function (name, fn) {
    const frame = { befores: [] };
    frames.push(frame);
    try { fn(); } finally { frames.pop(); }
  };
  global.it = function (name, fn) {
    const befores = [];
    for (const f of frames) befores.push(...f.befores);
    const ctx = {};
    try {
      for (const b of befores) b.call(ctx);
      fn.call(ctx);
      results.push({ classname: 'functional/project', name: 'project: ' + name, ok: true });
    } catch (e) {
      results.push({ classname: 'functional/project', name: 'project: ' + name, ok: false,
                     message: (e && (e.message || String(e))) || 'failed' });
    }
  };
  global.beforeEach = function (fn) { frames[frames.length - 1].befores.push(fn); };
  try {
    require(path.join(__dirname, '..', 'functional', 'project', 'serialize.js'));
  } catch (e) {
    results.push({ classname: 'harness', name: 'project suite loads', ok: false,
                   message: String((e && (e.stack || e.message)) || e) });
  } finally {
    delete global.describe; delete global.it; delete global.beforeEach;
  }
}

function main() {
  const results = [];
  let serialize;
  try {
    serialize = require(PRODUCT);
    if (typeof serialize !== 'function') throw new Error('the package entry point is not a function');
  } catch (e) {
    results.push({ classname: 'harness', name: 'product entry point loads', ok: false,
                   message: `could not load ${PRODUCT}: ${(e && e.message) || e}` });
    writeXml(results);
    return;
  }

  const mods = GROUP === 'functional'
    ? [path.join(__dirname, '..', 'functional', 'cases.js')]
    : [path.join(__dirname, '..', 'security', 'cases.js')];

  for (const mod of mods) {
    let entries;
    try {
      entries = require(mod)(serialize);
    } catch (e) {
      results.push({ classname: 'harness', name: `suite loads: ${path.basename(mod)}`, ok: false,
                     message: String((e && (e.stack || e.message)) || e) });
      continue;
    }
    for (const entry of entries) {
      try {
        entry.run();
        results.push({ classname: entry.classname, name: entry.name, ok: true });
      } catch (e) {
        results.push({ classname: entry.classname, name: entry.name, ok: false,
                       message: (e && (e.stack || e.message)) || String(e) });
      }
    }
  }

  if (GROUP === 'functional') runProjectSuite(results);

  writeXml(results);
}

main();
