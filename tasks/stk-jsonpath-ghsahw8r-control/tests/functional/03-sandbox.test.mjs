import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

test('sandbox variables, sandbox functions and a sandbox entry named arguments still work', () => {
    const json = {
        store: {
            book: {category: 'reference'},
            books: [{category: 'fiction'}, {category: 'travel'}]
        }
    };

    const byVariable = JSONPath({
        json: json,
        path: '$..[?(@.category === category)]',
        sandbox: {category: 'reference'},
        wrap: false
    });
    assert.deepEqual(byVariable, [json.store.book]);

    const byFunction = JSONPath({
        json: json,
        path: '$..[?(@.category === category())]',
        sandbox: {
            category () {
                return 'reference';
            }
        },
        wrap: false
    });
    assert.deepEqual(byFunction, [json.store.book]);

    const byFilter = JSONPath({
        json: json,
        path: '$..books[?(filter(@))]',
        sandbox: {
            filter (item) {
                return item.category === 'fiction';
            }
        },
        wrap: false
    });
    assert.deepEqual(byFilter, [json.store.books[0]]);

    const byArguments = JSONPath({
        json: json,
        path: '$..[?(@.category === arguments)]',
        sandbox: {arguments: 'reference'},
        wrap: false
    });
    assert.deepEqual(byArguments, [json.store.book]);
});
