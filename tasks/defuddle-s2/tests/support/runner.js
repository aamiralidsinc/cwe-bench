#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner for the defuddle task.
 *
 *     node runner.js <security|functional> <output.xml>
 *
 * The product is loaded from the submitted workspace through its real public API: the
 * TypeScript entry module src/node.ts is bundled with esbuild (the product's own build
 * toolchain), and the resulting module is evaluated in this process. Documents are parsed
 * with linkedom, the same DOM implementation the project's own tests use by default.
 * A case either throws (failure) or returns (pass).
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const WORKSPACE = process.env.WORKSPACE_DIR || '/workspace';
const MODULES = process.env.VERIFIER_MODULES || '/opt/verifier/node_modules';
const HERE = __dirname;

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

function loadProduct() {
  const esbuild = require(path.join(MODULES, 'esbuild'));
  return esbuild.build({
    entryPoints: [path.join(WORKSPACE, 'src', 'node.ts')],
    absWorkingDir: WORKSPACE,
    bundle: true,
    write: false,
    format: 'cjs',
    platform: 'node',
    target: 'node20',
    logLevel: 'silent',
    nodePaths: [MODULES],
    // These are the product's runtime dependencies; the verifier image provides them at a
    // fixed path so the submitted tree does not need node_modules.
    external: ['linkedom', 'turndown', 'mathml-to-latex', 'temml', 'commander'],
  }).then((built) => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'defuddle-hidden-'));
    const file = path.join(dir, 'product.cjs');
    fs.writeFileSync(file, built.outputFiles[0].text);
    try {
      return require(file);
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
}

async function main() {
  const results = [];
  let product;
  try {
    product = await loadProduct();
    if (typeof product.Defuddle !== 'function' || typeof product.DefuddleClass !== 'function') {
      throw new Error('the product does not expose its parsing entry points');
    }
  } catch (e) {
    results.push({
      classname: 'harness',
      name: 'the product loads through its public entry point',
      ok: false,
      message: (e && (e.stack || e.message)) || String(e),
    });
    writeXml(results);
    return;
  }

  const harness = require(path.join(HERE, 'harness.js'));
  const casesModule = require(path.join(HERE, '..', GROUP, 'cases.js'));
  const ctx = {
    Defuddle: product.Defuddle,
    DefuddleClass: product.DefuddleClass,
    makeDoc: harness.makeDoc,
    assertNoExecutable: harness.assertNoExecutable,
    harness,
    WORKSPACE,
  };

  let cases;
  try {
    cases = casesModule(ctx);
  } catch (e) {
    results.push({
      classname: 'harness',
      name: 'the hidden cases load',
      ok: false,
      message: (e && (e.stack || e.message)) || String(e),
    });
    writeXml(results);
    return;
  }

  for (const entry of cases) {
    try {
      await entry.run();
      results.push({ classname: entry.classname || GROUP, name: entry.name, ok: true });
    } catch (e) {
      results.push({
        classname: entry.classname || GROUP,
        name: entry.name,
        ok: false,
        message: (e && (e.stack || e.message)) || String(e),
      });
    }
  }
  writeXml(results);
}

main().catch((e) => {
  // A crash here is a runner defect; still emit a failure so the group is not silently empty.
  writeXml([{ classname: 'harness', name: 'runner completed', ok: false, message: (e && (e.stack || e.message)) || String(e) }]);
});
