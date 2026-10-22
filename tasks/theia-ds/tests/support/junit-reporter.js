'use strict';

// Minimal JUnit XML reporter (the bundled third-party reporter is not
// compatible with the repository's mocha version). score.py reads
// <testcase classname=... name=...> and treats <failure>/<error> as a failure.
const fs = require('fs');

function esc(value) {
    return String(value === undefined || value === null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

module.exports = function JUnitReporter(runner) {
    const results = [];

    runner.on('pass', test => results.push({ test, state: 'pass' }));
    runner.on('fail', (test, err) => results.push({ test, state: 'fail', err }));
    runner.on('pending', test => results.push({ test, state: 'pending' }));

    runner.on('end', () => {
        const output = process.env.JUNIT_OUTPUT;
        if (!output) {
            return;
        }
        const failures = results.filter(entry => entry.state === 'fail').length;
        const skipped = results.filter(entry => entry.state === 'pending').length;
        const cases = results.map(entry => {
            const test = entry.test || {};
            const classname = typeof test.parentFullTitle === 'function'
                ? test.parentFullTitle()
                : (test.parent && typeof test.parent.fullTitle === 'function' ? test.parent.fullTitle() : '');
            const name = test.title || test.fullTitle || 'unknown';
            let body = '';
            if (entry.state === 'fail') {
                const err = entry.err || {};
                body = `<failure message="${esc(err.message || 'failed')}">${esc(err.stack || err.message || '')}</failure>`;
            } else if (entry.state === 'pending') {
                body = '<skipped/>';
            }
            return `<testcase classname="${esc(classname)}" name="${esc(name)}">${body}</testcase>`;
        }).join('\n');
        const xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            + `<testsuite name="mocha" tests="${results.length}" failures="${failures}" skipped="${skipped}" errors="0">\n`
            + cases + '\n</testsuite>\n';
        fs.mkdirSync(require('path').dirname(output), { recursive: true });
        fs.writeFileSync(output, xml);
    });
};
