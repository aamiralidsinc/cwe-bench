import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-node.js';

function query (path, json) {
    JSONPath.cache = {};
    try {
        return {threw: false, result: JSONPath({json: json, path: path, wrap: false})};
    } catch (e) {
        return {threw: true, result: undefined};
    }
}

test('the Node build default mode does not run a query in the host engine', () => {
    // `this` has meaning only to the host language engine. The restricted
    // interpreter rejects it, so a returned match means the query ran natively.
    const out = query('$[?(this)]', [{a: 1}]);
    const ranNatively = !out.threw && Array.isArray(out.result) && out.result.length > 0;
    assert.strictEqual(ranNatively ? 1 : 0, 0, 'a query escaped to the host engine');
});

test('the Node build cannot reach a code-constructing object from the data', () => {
    delete globalThis.__jsonpathNodeProbe;
    const code = 'globalThis.__jsonpathNodeProbe = (globalThis.__jsonpathNodeProbe || 0) + 1';
    const out = query(
        `$[?(@.constructor.constructor(${JSON.stringify(code)})() === undefined)]`,
        [{a: 1}]
    );
    const ran = !out.threw && Array.isArray(out.result) && out.result.length > 0;
    const marks = globalThis.__jsonpathNodeProbe || 0;
    delete globalThis.__jsonpathNodeProbe;
    assert.strictEqual(ran ? 1 : 0, 0, 'a query reached a code-constructing object');
    assert.strictEqual(marks, 0, 'code from the query ran');
});
