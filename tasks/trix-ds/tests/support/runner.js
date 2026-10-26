#!/usr/bin/env node
'use strict';

/*
 * Hidden-suite runner.
 *
 *     node runner.js <security|functional> <output.xml>
 *
 * The product is loaded from the submitted workspace through its real public APIs: the source
 * modules are bundled with esbuild and evaluated on a jsdom document, the prebuilt asset shipped
 * with the repository is evaluated on a jsdom document, and the project's own unit suite is run
 * from a pristine copy of the pinned test files. Each case either throws (failure) or returns
 * (pass). Expected values are literals in the case tables; nothing is computed with the product.
 */

const fs = require('fs');
const path = require('path');

const GROUP = process.argv[2];
const OUT = process.argv[3];
const WORKSPACE = process.env.WORKSPACE_DIR || '/workspace';
const MODULES = process.env.VERIFIER_MODULES || '/opt/verifier/node_modules';
const HERE = __dirname;
const PROJECT_TEST = path.join(HERE, '..', 'functional', 'project', 'test');

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

function failResult(classname, name, error) {
  return {
    classname,
    name,
    ok: false,
    message: (error && (error.stack || error.message)) || String(error),
  };
}

function makeDom() {
  const { JSDOM, VirtualConsole } = require('jsdom');
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', () => {});
  const dom = new JSDOM(
    '<!doctype html><html><head></head><body><div id="qunit"></div><div id="qunit-fixture"></div></body></html>',
    { url: 'http://example.test/', runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole },
  );
  const w = dom.window;
  w.scrollTo = function () {};
  try { w.focus = function () {}; } catch (_) { /* ignored */ }
  return w;
}

let bundleCounter = 0;

async function bundle(entrySource) {
  const esbuild = require('esbuild');
  const tmpdir = fs.mkdtempSync('/tmp/trix-hidden-');
  const entry = path.join(tmpdir, `entry-${bundleCounter += 1}.js`);
  fs.writeFileSync(entry, entrySource);
  const projectRelative = {
    name: 'project-relative-product',
    setup(build) {
      // Two project test files reach the product with a path relative to the repository's src/
      // directory; the pristine test copy has no src/ neighbour, so point those at the submission.
      build.onResolve({ filter: /^\.\.\/\.\.\/trix(\/|$)/ }, (args) => {
        if (!path.resolve(args.resolveDir).startsWith(PROJECT_TEST)) return null;
        const relative = args.path.replace(/^\.\.\/\.\.\/trix\/?/, '');
        let target = path.join(WORKSPACE, 'src', 'trix', relative);
        try {
          if (fs.statSync(target).isDirectory()) target = path.join(target, 'index.js');
        } catch (_) { /* let esbuild report it */ }
        return { path: target };
      });
    },
  };
  const out = await esbuild.build({
    entryPoints: [entry],
    bundle: true,
    write: false,
    format: 'iife',
    globalName: 'TRIX_PRODUCT',
    platform: 'browser',
    target: 'es2020',
    logLevel: 'silent',
    absWorkingDir: WORKSPACE,
    nodePaths: [MODULES],
    plugins: [projectRelative],
    alias: {
      trix: path.join(WORKSPACE, 'src', 'trix'),
      test: PROJECT_TEST,
      trix_editor_element: path.join(WORKSPACE, 'src', 'trix', 'elements', 'trix_editor_element.js'),
      trix_toolbar_element: path.join(WORKSPACE, 'src', 'trix', 'elements', 'trix_toolbar_element.js'),
      event_helpers: path.join(PROJECT_TEST, 'test_helpers', 'event_helpers.js'),
    },
  });
  fs.rmSync(tmpdir, { recursive: true, force: true });
  return out.outputFiles[0].text;
}

const PRODUCT_ENTRY = `
import Document from "trix/models/document"
import HTMLParser from "trix/models/html_parser"
import StringPiece from "trix/models/string_piece"
import AttachmentPiece from "trix/models/attachment_piece"
import { deserializeFromContentType, serializeToContentType } from "trix/core/serialization"
import DocumentView from "trix/views/document_view"
export { Document, HTMLParser, StringPiece, AttachmentPiece, deserializeFromContentType, serializeToContentType, DocumentView }
`;

const PROJECT_ENTRY = `
import "trix/trix"
import "test/test_helper"
import "test/unit"
`;

function loadProduct(w) {
  return bundle(PRODUCT_ENTRY).then((code) => {
    w.eval(code);
    return w.TRIX_PRODUCT;
  });
}

async function runCaseList(entries) {
  const results = [];
  for (const entry of entries) {
    if (entry.precomputed) {
      results.push({
        classname: entry.classname,
        name: entry.name,
        ok: entry.precomputed.ok,
        message: entry.precomputed.message,
      });
      continue;
    }
    try {
      await entry.run();
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
  return results;
}

async function securityResults(results) {
  let w, T;
  try {
    w = makeDom();
    T = await loadProduct(w);
  } catch (e) {
    results.push(failResult('harness', 'the product loads through its public entry point', e));
    return;
  }
  const cases = require(path.join(HERE, '..', 'security', 'cases.js'));
  results.push(...await runCaseList(cases({ document: w.document, window: w, T, bundle })));

  let bw;
  try {
    bw = makeDom();
    const asset = path.join(WORKSPACE, 'action_text-trix', 'app', 'assets', 'javascripts', 'trix.js');
    bw.eval(fs.readFileSync(asset, 'utf8'));
    if (!bw.Trix || !bw.Trix.Document || !bw.Trix.views || !bw.Trix.views.DocumentView) {
      throw new Error('the prebuilt asset does not expose the document API');
    }
  } catch (e) {
    results.push(failResult('harness', 'the prebuilt asset loads', e));
    bw = null;
  }
  if (bw) {
    const bundleCases = require(path.join(HERE, '..', 'security', 'bundle_cases.js'));
    results.push(...await runCaseList(bundleCases({ document: bw.document, window: bw, Trix: bw.Trix })));
  }

  let htmlW;
  try {
    htmlW = makeDom();
  } catch (e) {
    results.push(failResult('harness', 'the markup parser environment loads', e));
    htmlW = null;
  }
  if (htmlW) {
    let htmlT = null;
    try {
      htmlT = await loadProduct(htmlW);
    } catch (e) {
      results.push(failResult('harness', 'the product loads for markup entry points', e));
    }
    if (htmlT) {
      const markupCases = require(path.join(HERE, '..', 'security', 'markup_cases.js'));
      results.push(...await runCaseList(markupCases({ document: htmlW.document, window: htmlW, T: htmlT })));
    }
  }
}

async function projectResults() {
  const w = makeDom();
  const results = [];
  const qunitPath = path.join(MODULES, 'qunit', 'qunit', 'qunit.js');
  w.eval(fs.readFileSync(qunitPath, 'utf8'));
  w.eval('QUnit.config.autostart = false; QUnit.config.hidepassed = true; QUnit.config.testTimeout = 20000;');

  const SKIP = /bidirection|bidrectional|detects text direction|translates block element margins|skips translating empty block element margins|keeps custom tags configured for DOMPurify/i;

  let seq = 0;
  const done = new Promise((resolve) => {
    w.QUnit.testDone((t) => {
      seq += 1;
      if (SKIP.test(`${t.module || ''} ${t.name || ''}`)) return;
      results.push({
        classname: `project/${t.module || 'root'}`,
        name: `${t.name} #${seq}`,
        ok: t.failed === 0,
        message: t.failed === 0 ? undefined : `${t.failed} of ${t.total} assertions failed in ${t.module || 'root'} :: ${t.name}`,
      });
    });
    w.QUnit.done((d) => resolve(d));
  });

  const code = await bundle(PROJECT_ENTRY);
  w.eval(code);
  const timer = setTimeout(() => resolve({ status: 'timeout' }), 150000);
  w.QUnit.start();
  const summary = await done;
  clearTimeout(timer);
  if (!results.length) {
    results.push(failResult('harness', 'the project suite ran', new Error(`no test results (${JSON.stringify(summary)})`)));
  }
  return results;
}

async function functionalResults(results) {
  let w, T;
  try {
    w = makeDom();
    T = await loadProduct(w);
  } catch (e) {
    results.push(failResult('harness', 'the product loads through its public entry point', e));
    return;
  }
  const cases = require(path.join(HERE, '..', 'functional', 'cases.js'));
  results.push(...await runCaseList(cases({ document: w.document, window: w, T })));

  let bw;
  try {
    bw = makeDom();
    const asset = path.join(WORKSPACE, 'action_text-trix', 'app', 'assets', 'javascripts', 'trix.js');
    bw.eval(fs.readFileSync(asset, 'utf8'));
    if (!bw.Trix || !bw.Trix.Document || !bw.Trix.views || !bw.Trix.views.DocumentView) {
      throw new Error('the prebuilt asset does not expose the document API');
    }
    const bundleCases = require(path.join(HERE, '..', 'functional', 'bundle_cases.js'));
    results.push(...await runCaseList(bundleCases({ document: bw.document, window: bw, Trix: bw.Trix })));
  } catch (e) {
    results.push(failResult('harness', 'the prebuilt asset renders', e));
  }

  try {
    results.push(...await projectResults());
  } catch (e) {
    results.push(failResult('harness', 'the project suite runs', e));
  }
}

async function main() {
  const results = [];
  try {
    if (GROUP === 'security') {
      await securityResults(results);
    } else if (GROUP === 'functional') {
      await functionalResults(results);
    } else {
      throw new Error(`unknown group ${GROUP}`);
    }
  } catch (e) {
    results.push(failResult('harness', 'runner', e));
  }
  writeXml(results);
  process.exit(0);
}

main().catch((e) => {
  try {
    writeXml([failResult('harness', 'runner', e)]);
  } catch (_) {
    process.exitCode = 1;
  }
  process.exit(0);
});
