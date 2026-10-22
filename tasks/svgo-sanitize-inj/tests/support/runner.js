'use strict';
// Shared harness for the hidden svgo sanitation tests.
//
// Every test drives the real public entry point: the library's optimize() API
// with the opt-in sanitation pass enabled, exactly as an application that
// sanitizes untrusted uploads would call it. A test is a { name, run } pair;
// run(ctx) throws to fail. Results are written as JUnit XML so score.py can
// read them. No product code is used to compute expectations: assertions are
// plain string/structure checks on the returned document.

const fs = require('fs');
const path = require('path');

const { optimize } = require(process.env.SVGO_ENTRY || '/app/lib/svgo.js');

// Run the SVG through the sanitation pass (and nothing else), twice, so a fix
// that is not idempotent is still judged on its stable output.
function sanitize(svg) {
  const result = optimize(svg, {
    plugins: ['removeScriptElement'],
    multipass: true,
    js2svg: { pretty: false },
  });
  if (result.error) {
    throw new Error('optimize reported an error: ' + result.error);
  }
  if (typeof result.data !== 'string') {
    throw new Error('optimize returned no document');
  }
  return result.data;
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

// Assert a substring is absent (case-insensitive). Used to prove an attack
// construct was neutralized, regardless of how a correct fix removes it.
function refuteContains(haystack, needle, msg) {
  assert(
    !haystack.toLowerCase().includes(needle.toLowerCase()),
    (msg || 'must not contain') + ' [' + needle + ']\n  got: ' + haystack,
  );
}

function assertContains(haystack, needle, msg) {
  assert(
    haystack.includes(needle),
    (msg || 'expected to contain') + ' [' + needle + ']\n  got: ' + haystack,
  );
}

function xmlEscape(s) {
  return String(s).replace(/[<&>"']/g, (c) =>
    ({ '<': '&lt;', '&': '&amp;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]),
  );
}

function runSuite(suiteName, cases, outFile) {
  const ctx = { sanitize, assert, refuteContains, assertContains };
  const results = [];
  for (const c of cases) {
    const start = Date.now();
    let failure = null;
    try {
      c.run(ctx);
    } catch (e) {
      failure = e && e.stack ? e.stack : String(e);
    }
    results.push({ name: c.name, time: (Date.now() - start) / 1000, failure });
    const tag = failure ? 'FAIL' : 'ok';
    process.stdout.write(`[${tag}] ${suiteName} :: ${c.name}\n`);
    if (failure) process.stdout.write('    ' + failure.split('\n')[0] + '\n');
  }
  const fails = results.filter((r) => r.failure).length;
  const body = results
    .map((r) => {
      const open = `  <testcase classname="${xmlEscape(suiteName)}" name="${xmlEscape(r.name)}" time="${r.time}">`;
      if (!r.failure) return open + '</testcase>';
      return (
        open +
        `\n    <failure message="assertion failed">${xmlEscape(r.failure)}</failure>\n  </testcase>`
      );
    })
    .join('\n');
  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<testsuite name="${xmlEscape(suiteName)}" tests="${results.length}" failures="${fails}">\n` +
    body +
    `\n</testsuite>\n`;
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, xml);
  process.stdout.write(`${suiteName}: ${results.length - fails}/${results.length} passed -> ${outFile}\n`);
}

module.exports = { runSuite };
