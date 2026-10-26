'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');

describe('preservation: string-parameter mode', function() {
  it('passes number and boolean arguments with their own types', function() {
    const template = Handlebars.compile('{{show 0 false 12}}', {
      stringParams: true
    });
    const out = template(
      {},
      {
        helpers: {
          show: function(zero, no, twelve) {
            return [typeof zero, zero, typeof no, no, typeof twelve, twelve].join('|');
          }
        }
      }
    );
    assert.strictEqual(out, 'number|0|boolean|false|number|12');
  });

  it('normalises the source text of a path argument', function() {
    const template = Handlebars.compile('{{show ./a/b ../c/d}}', {
      stringParams: true
    });
    const seen = [];
    template(
      { a: { b: 1 }, x: 2 },
      {
        helpers: {
          show: function(first, second) {
            seen.push(String(first), String(second));
            return '';
          }
        }
      }
    );
    assert.deepStrictEqual(seen, ['a.b', 'c.d']);
  });
});
