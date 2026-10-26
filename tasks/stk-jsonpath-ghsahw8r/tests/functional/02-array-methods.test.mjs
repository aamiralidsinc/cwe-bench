import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

test('array methods on literals still evaluate', () => {
    const json = {store: {book: {category: 'book'}, books: {category: 'books'}}};
    const found = JSONPath({
        json: json,
        path: '$..[?(["book", "books"].includes(@property))]',
        wrap: false
    });
    assert.deepEqual(found, [json.store.book, json.store.books]);
});
