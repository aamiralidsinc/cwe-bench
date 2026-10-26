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

test('a nested filter path step cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathNestedProbe;
    const code = 'globalThis.__jsonpathNestedProbe = ' +
        '(globalThis.__jsonpathNestedProbe || 0) + 1; return "getPrototypeOf"';
    const inner = '@.getOwnPropertyDescriptor(@.getPrototypeOf(@), "constructor")' +
        `.value(${JSON.stringify(code)})()`;
    const out = query(
        `$[?(@.constructor[(${inner})])]`,
        [{a: 1}, {b: 2}]
    );
    const marks = globalThis.__jsonpathNestedProbe || 0;
    delete globalThis.__jsonpathNestedProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});
