#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node --import tsx runner.js <security|functional> <output.xml>
 *
 * Loads the product through its public entry point (the package's exported
 * Address4/Address6 classes), runs every case in the group, and writes a JUnit
 * XML file the scorer reads. A case either throws (failure) or returns
 * normally (pass). Expected values are literals in the case tables; no product
 * code is used to compute them.
 */

const fs = require('fs');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const PRODUCT = process.env.PRODUCT_ENTRY || '/workspace/src/ip-address';

function esc(s) {
  return String(s)
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

async function main() {
  const results = [];
  let product;
  try {
    product = require(PRODUCT);
    if (typeof product.Address4 !== 'function' || typeof product.Address6 !== 'function') {
      throw new Error('the product did not expose the address classes');
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

  const mod = path.join(__dirname, '..', GROUP, 'cases.js');
  let entries;
  try {
    entries = require(mod)(product);
  } catch (e) {
    results.push({
      classname: 'harness',
      name: `suite loads: ${path.basename(mod)}`,
      ok: false,
      message: `suite error: ${e && (e.stack || e.message)}`,
    });
    writeXml(results);
    return;
  }

  for (const entry of entries) {
    try {
      entry.run();
      results.push({ classname: entry.classname, name: entry.name, ok: true });
    } catch (e) {
      results.push({
        classname: entry.classname,
        name: entry.name,
        ok: false,
        message: (e && e.message) || String(e),
      });
    }
  }

  writeXml(results);
}

main().catch((e) => {
  try {
    writeXml([{ classname: 'harness', name: 'runner', ok: false, message: String(e && (e.stack || e.message)) }]);
  } catch (_) {
    process.exitCode = 1;
  }
});
