import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

test('the built-in query variables still resolve', () => {
    const json = {
        store: {
            book: [
                {category: 'reference', price: 8},
                {category: 'fiction', price: 22}
            ]
        }
    };

    const byParent = JSONPath({
        json: json,
        path: '$.store.book[?(@.price > 10 && @parent)]',
        wrap: false
    });
    assert.deepEqual(byParent, [json.store.book[1]]);

    const byRoot = JSONPath({
        json: json,
        path: '$.store.book[?(@root.store.book.length === 2)]',
        wrap: false
    });
    assert.deepEqual(byRoot, json.store.book);

    const byProperty = JSONPath({
        json: json,
        path: '$.store[?(@property === "book" && @.length === 2)]',
        wrap: false
    });
    assert.deepEqual(byProperty, [json.store.book]);
});
