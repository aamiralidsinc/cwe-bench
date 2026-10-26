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

test('a computed property given as a non-string value cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathArrayKeyProbe;
    const code = 'globalThis.__jsonpathArrayKeyProbe = ' +
        '(globalThis.__jsonpathArrayKeyProbe || 0) + 1';
    const out = query(
        `$[?(@[["constructor"]][["constructor"]](${JSON.stringify(code)})() === undefined)]`,
        [{a: 1}]
    );
    const marks = globalThis.__jsonpathArrayKeyProbe || 0;
    delete globalThis.__jsonpathArrayKeyProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});

test('a computed property assembled at run time cannot reach a code-constructing object', () => {
    delete globalThis.__jsonpathBuiltKeyProbe;
    const code = 'globalThis.__jsonpathBuiltKeyProbe = ' +
        '(globalThis.__jsonpathBuiltKeyProbe || 0) + 1';
    const out = query(
        `$[?(@["con" + "structor"]["con" + "structor"](${JSON.stringify(code)})() === undefined)]`,
        [{a: 1}]
    );
    const marks = globalThis.__jsonpathBuiltKeyProbe || 0;
    delete globalThis.__jsonpathBuiltKeyProbe;
    assert.strictEqual(marks, 0, 'code from the query ran');
});
