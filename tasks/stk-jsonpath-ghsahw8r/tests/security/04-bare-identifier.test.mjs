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

test('a bare identifier cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathIdentifierProbe;
    const code = 'globalThis.__jsonpathIdentifierProbe = ' +
        '(globalThis.__jsonpathIdentifierProbe || 0) + 1';
    const out = query(
        '$[?(constructor.getOwnPropertyDescriptor(' +
            'constructor.getPrototypeOf(constructor), "constructor")' +
            `.value(${JSON.stringify(code)})() === undefined)]`,
        [{a: 1}]
    );
    const marks = globalThis.__jsonpathIdentifierProbe || 0;
    delete globalThis.__jsonpathIdentifierProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});
