import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-node.js';

test('the Node build still evaluates ordinary filters and sandbox calls', () => {
    const json = {
        store: {
            book: [
                {category: 'reference', price: 8},
                {category: 'fiction', price: 22}
            ]
        }
    };

    JSONPath.cache = {};
    const filtered = JSONPath({
        json: json,
        path: '$..book[?(@.price < 10)]',
        wrap: false
    });
    assert.deepEqual(filtered, [json.store.book[0]]);

    JSONPath.cache = {};
    const sandboxed = JSONPath({
        json: json,
        path: '$..book[?(cheap(@))]',
        sandbox: {
            cheap (item) {
                return item.price < 10;
            }
        },
        wrap: false
    });
    assert.deepEqual(sandboxed, [json.store.book[0]]);
});
