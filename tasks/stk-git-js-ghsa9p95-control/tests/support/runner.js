#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner. Usage:
 *     node runner.js <security|functional> <output.xml>
 *
 * Loads the library through its public entry point, runs every case in the group against a real
 * local git, and writes a JUnit XML file the scorer reads. A case that throws is a failure; a case
 * that returns is a pass. Expected values and every repository/marker are created by the cases
 * themselves; nothing is computed with product code.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const cp = require('child_process');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const PRODUCT = process.env.PRODUCT_ENTRY || '/workspace/.htests/product.cjs';

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

function environment(root) {
  const home = path.join(root, 'home');
  fs.mkdirSync(home, { recursive: true });
  const gitconfig = path.join(home, 'gitconfig');
  fs.writeFileSync(gitconfig, '');
  process.env.HOME = home;
  process.env.GIT_CONFIG_NOSYSTEM = '1';
  process.env.GIT_CONFIG_GLOBAL = gitconfig;
  process.env.GIT_TERMINAL_PROMPT = '0';

  return {
    fs,
    os,
    path,
    cp,
    root,
    sh(cmd, args, cwd) {
      return cp.execFileSync(cmd, args, { cwd, stdio: 'pipe' });
    },
    markerFor(id) {
      const marker = path.join(root, `marker-${id}`);
      const script = path.join(root, `program-${id}.sh`);
      fs.writeFileSync(script, `#!/bin/sh\ntouch '${marker}'\nexit 1\n`);
      fs.chmodSync(script, 0o755);
      return {
        marker,
        script,
        reset() {
          try { fs.rmSync(marker, { force: true }); } catch (_) { /* ignore */ }
        },
        exists() {
          return fs.existsSync(marker);
        },
      };
    },
    unique(name) {
      return path.join(root, `${name}-${Math.random().toString(36).slice(2)}`);
    },
  };
}

async function main() {
  const results = [];
  let product;
  try {
    const mod = require(PRODUCT);
    product = typeof mod === 'function' ? mod : mod && mod.default;
    if (typeof product !== 'function') {
      throw new Error('the library did not expose its factory');
    }
  } catch (e) {
    results.push({
      classname: 'harness',
      name: 'library entry point loads',
      ok: false,
      message: `could not load ${PRODUCT}: ${e && (e.stack || e.message)}`,
    });
    writeXml(results);
    return;
  }

  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'gitjs-hidden-'));
  const ctx = environment(root);
  ctx.simpleGit = product;

  const modules = GROUP === 'functional'
    ? [path.join(__dirname, '..', 'functional', 'cases.js')]
    : [path.join(__dirname, '..', 'security', 'cases.js')];

  for (const mod of modules) {
    let entries;
    try {
      entries = await require(mod)(ctx);
    } catch (e) {
      results.push({
        classname: 'harness',
        name: `suite loads: ${path.basename(mod)}`,
        ok: false,
        message: `suite error: ${e && (e.stack || e.message)}`,
      });
      continue;
    }
    for (const entry of entries) {
      try {
        await entry.run();
        results.push({ classname: entry.classname, name: entry.name, ok: true });
      } catch (e) {
        results.push({
          classname: entry.classname,
          name: entry.name,
          ok: false,
          message: (e && (e.message || String(e))) || String(e),
        });
      }
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
