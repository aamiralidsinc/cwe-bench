import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

test('regular-expression and string methods on values still evaluate', () => {
    const json = {
        store: {
            book: [
                {category: 'reference', title: 'A'},
                {category: 'fiction', title: 'B'},
                {category: 'non-fiction', title: 'C'}
            ]
        }
    };
    const byPattern = JSONPath({
        json: json,
        path: '$..book[?(@.category.match(/TION$/i))]',
        wrap: false
    });
    assert.deepEqual(byPattern, [json.store.book[1], json.store.book[2]]);

    const byLower = JSONPath({
        json: json,
        path: '$..book[?(@.category.toLowerCase() === "reference")]',
        wrap: false
    });
    assert.deepEqual(byLower, [json.store.book[0]]);
});
