import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

function query (path, json, opts = {}) {
    JSONPath.cache = {};
    try {
        return {
            threw: false,
            result: JSONPath({json: json, path: path, wrap: false, ...opts})
        };
    } catch (e) {
        return {threw: true, result: undefined};
    }
}

test('a member read on evaluated data cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathMemberProbe;
    const code = 'globalThis.__jsonpathMemberProbe = ' +
        '(globalThis.__jsonpathMemberProbe || 0) + 1';
    const out = query(
        `$[?(@.constructor.constructor(${JSON.stringify(code)})() === undefined)]`,
        [{a: 1}]
    );
    const marks = globalThis.__jsonpathMemberProbe || 0;
    delete globalThis.__jsonpathMemberProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});

test('a member read named through another member cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathNamedProbe;
    const code = 'globalThis.__jsonpathNamedProbe = ' +
        '(globalThis.__jsonpathNamedProbe || 0) + 1';
    const out = query(
        `$[?(@[["constructor"][0]][["constructor"][0]](${JSON.stringify(code)})() === undefined)]`,
        [{a: 1}]
    );
    const marks = globalThis.__jsonpathNamedProbe || 0;
    delete globalThis.__jsonpathNamedProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});

test('a dynamic property step cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathStepProbe;
    const code = 'globalThis.__jsonpathStepProbe = ' +
        '(globalThis.__jsonpathStepProbe || 0) + 1; return "marker"';
    const out = query(
        `$[(@.constructor.constructor(${JSON.stringify(code)})())]`,
        {marker: 'present'}
    );
    const marks = globalThis.__jsonpathStepProbe || 0;
    delete globalThis.__jsonpathStepProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});
