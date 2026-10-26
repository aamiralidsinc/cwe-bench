import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

test('an expression used as a dynamic path step still evaluates', () => {
    const json = [{id: 1}, {id: 2}, {id: 3}];
    const last = JSONPath({json: json, path: '$[(@.length-1)].id', wrap: false});
    assert.deepEqual(last, 3);

    const first = JSONPath({json: json, path: '$[(0)].id', wrap: false});
    assert.deepEqual(first, 1);
});

test('nested filter expressions still select their matches', () => {
    const json = {
        name: 'root',
        children: [
            {name: 'child1', grand_children: [{name: 'child1_1'}]},
            {name: 'child2', grand_children: [{name: 'child2_1'}]}
        ]
    };
    const found = JSONPath({
        json: json,
        path: '$..children[?(@.grand_children[?(@.name === "child2_1")])]',
        wrap: false
    });
    assert.deepEqual(found, [json.children[1]]);

    const draft = {
        a: [3, 5, 1, 2, 4, 6, {b: 'j'}, {b: 'k'}, {b: {}}, {b: 'kilo'}],
        o: {p: 1, q: 2, r: 3, s: 5, t: {u: 6}},
        e: 'f'
    };
    const draftFound = JSONPath({
        json: draft,
        path: '$[?(@[?(@.b)])]',
        wrap: false
    });
    assert.deepEqual(draftFound, [draft.a]);
});
