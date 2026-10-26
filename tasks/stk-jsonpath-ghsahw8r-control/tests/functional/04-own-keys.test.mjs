import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSONPath} from '../../src/jsonpath-browser.js';

test('data may have own properties named like prototype members', () => {
    const json = JSON.parse(
        '[{"constructor": "own-constructor", "__proto__": "own-proto", "a": 1},' +
        ' {"constructor": "other", "__proto__": "other", "a": 2}]'
    );
    assert.deepEqual(
        Object.keys(json[0]).sort(),
        ['__proto__', 'a', 'constructor'],
        'the fixture stores both names as own properties'
    );

    const byConstructor = JSONPath({
        json: json,
        path: '$[?(@.constructor === "own-constructor")]',
        wrap: false
    });
    assert.deepEqual(byConstructor, [json[0]]);

    const byProto = JSONPath({
        json: json,
        path: '$[?(@.__proto__ === "own-proto")]',
        wrap: false
    });
    assert.deepEqual(byProto, [json[0]]);
});
