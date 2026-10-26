'use strict';
const { writeFileSync } = require('node:fs');
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;')
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '');
}
module.exports = function JUnitReporter(runner, options) {
  const out = (options && options.reporterOptions && options.reporterOptions.mochaFile) || process.env.JUNIT_OUT;
  const cases = [];
  let started = Date.now();
  runner.on('pass', t => cases.push({ t, state: 'pass' }));
  runner.on('fail', (t, err) => cases.push({ t, state: 'fail', err }));
  runner.on('pending', t => cases.push({ t, state: 'skipped' }));
  runner.on('end', () => {
    const failures = cases.filter(c => c.state === 'fail').length;
    const xml = ['<?xml version="1.0" encoding="UTF-8"?>',
      `<testsuite name="suite" tests="${cases.length}" failures="${failures}" errors="0" skipped="${cases.filter(c=>c.state==='skipped').length}" time="${(Date.now()-started)/1000}">`];
    for (const c of cases) {
      const title = c.t.fullTitle ? c.t.fullTitle() : (c.t.title || 'test');
      const cls = (c.t.parent && c.t.parent.fullTitle) ? c.t.parent.fullTitle() : 'root';
      xml.push(`<testcase classname="${esc(cls)}" name="${esc(title)}" time="0">`);
      if (c.state === 'fail') {
        const msg = c.err && (c.err.message || String(c.err)) || 'failed';
        xml.push(`<failure message="${esc(msg).slice(0, 2000)}">${esc((c.err && c.err.stack) || msg)}</failure>`);
      } else if (c.state === 'skipped') xml.push('<skipped/>');
      xml.push('</testcase>');
    }
    xml.push('</testsuite>');
    writeFileSync(out, xml.join('\n'));
  });
};
