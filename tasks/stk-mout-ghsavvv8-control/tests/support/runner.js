#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Loads the library through its real public modules with the project's own AMD loader, runs every
 * case in the group, and writes a JUnit XML file the scorer reads. A case throws (failure) or
 * returns normally (pass). Expected values are literals in the case tables; no product code is
 * used to compute them.
 */

const fs = require('fs');
const path = require('path');
const requirejs = require('requirejs');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const ROOT = process.env.PRODUCT_ROOT || '/workspace';

const MODULES = {
  deepMixIn: 'mout/object/deepMixIn',
  deepFillIn: 'mout/object/deepFillIn',
  set: 'mout/object/set',
  namespace: 'mout/object/namespace',
  unset: 'mout/object/unset',
  get: 'mout/object/get',
  has: 'mout/object/has',
};

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

function harnessFailure(message) {
  writeXml([{ classname: 'harness', name: 'product modules load', ok: false, message }]);
}

function runGroup(product) {
  const results = [];
  const mods = GROUP === 'functional'
    ? [path.join(__dirname, '..', 'functional', 'cases.js'),
       path.join(__dirname, '..', 'functional', 'project.js')]
    : [path.join(__dirname, '..', 'security', 'cases.js')];

  for (const mod of mods) {
    if (!fs.existsSync(mod)) continue;
    let entries;
    try {
      entries = require(mod)(product);
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
  if (!results.length) {
    results.push({ classname: 'harness', name: `suite empty: ${GROUP}`, ok: false, message: 'no cases ran' });
  }
  writeXml(results);
}

try {
  requirejs.config({ baseUrl: ROOT, paths: { mout: 'src' }, nodeRequire: require });
  const ids = Object.keys(MODULES).map((k) => MODULES[k]);
  requirejs(ids, function () {
    const product = {};
    Object.keys(MODULES).forEach((k, i) => { product[k] = arguments[i]; });
    runGroup(product);
  }, function (err) {
    harnessFailure(`could not load the library modules: ${err && (err.message || err)}`);
  });
} catch (e) {
  harnessFailure(`runner error: ${e && (e.stack || e.message)}`);
}
