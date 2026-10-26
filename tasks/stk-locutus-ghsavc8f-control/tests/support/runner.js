#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Loads the library's exported functions from PRODUCT_ROOT and runs every case in the group,
 * writing the JUnit XML the scorer reads. A case either throws (failure) or returns normally
 * (pass). Expected values are literals in the case tables; nothing is computed with the product.
 */

const fs = require('fs');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const PRODUCT_ROOT = process.env.PRODUCT_ROOT || '/workspace';

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

function productLoad(rel) {
  return require(path.join(PRODUCT_ROOT, 'src', 'php', rel));
}

function main() {
  const results = [];
  const probe = GROUP === 'functional' ? 'array/array_merge.js' : 'strings/parse_str.js';
  try {
    const fn = productLoad(probe);
    if (typeof fn !== 'function') {
      throw new Error('the exported module is not a function');
    }
  } catch (e) {
    results.push({
      classname: 'harness', name: 'product entry points load',
      ok: false, message: `could not load ${probe} from ${PRODUCT_ROOT}: ${e && e.message}`,
    });
    writeXml(results);
    return;
  }

  const mods = GROUP === 'functional'
    ? [path.join(__dirname, '..', 'functional', 'cases.js'),
       path.join(__dirname, '..', 'functional', 'project.js')]
    : [path.join(__dirname, '..', 'security', 'cases.js')];

  for (const mod of mods) {
    let entries;
    try {
      entries = require(mod)(productLoad);
    } catch (e) {
      results.push({
        classname: 'harness', name: `suite loads: ${path.basename(mod)}`,
        ok: false, message: `suite error: ${e && (e.stack || e.message)}`,
      });
      continue;
    }
    for (const entry of entries) {
      if (entry.precomputed) {
        results.push({
          classname: entry.classname, name: entry.name,
          ok: entry.precomputed.ok, message: entry.precomputed.message,
        });
        continue;
      }
      try {
        entry.run();
        results.push({ classname: entry.classname, name: entry.name, ok: true });
      } catch (e) {
        results.push({
          classname: entry.classname, name: entry.name, ok: false,
          message: (e && e.message) || String(e),
        });
      }
    }
  }

  writeXml(results);
}

try {
  main();
} catch (e) {
  try {
    writeXml([{ classname: 'harness', name: 'runner', ok: false, message: String(e && (e.stack || e.message)) }]);
  } catch (_) {
    process.exitCode = 1;
  }
}
