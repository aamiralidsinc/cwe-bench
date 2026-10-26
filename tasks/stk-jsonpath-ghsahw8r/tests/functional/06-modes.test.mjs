import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-node.js';

test('the explicit native and disabled evaluation modes keep their meaning', () => {
    JSONPath.cache = {};
    const nativeResult = JSONPath({
        json: [{a: 1}, {a: 2}],
        path: '$[?(this)]',
        eval: 'native',
        wrap: false
    });
    assert.deepEqual(nativeResult, [{a: 1}, {a: 2}]);

    JSONPath.cache = {};
    assert.throws(
        () => JSONPath({
            json: [{a: 1}],
            path: '$[?(@.a)]',
            eval: false,
            wrap: false
        }),
        /Eval \[\?\(expr\)\] prevented/
    );

    JSONPath.cache = {};
    const safeResult = JSONPath({
        json: [{a: 1}, {a: 2}],
        path: '$[?(@.a === 1)]',
        eval: 'safe',
        wrap: false
    });
    assert.deepEqual(safeResult, [{a: 1}]);
});
