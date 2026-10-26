'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');

describe('preservation: ordinary magnitude of numbers', function() {
  const huge = new Array(401).join('9');

  it('keeps a very large integer in template text working', function() {
    const template = Handlebars.compile('{{echo ' + huge + '}} {{echo -' + huge + '}}');
    const out = template(
      {},
      { helpers: { echo: function(value) { return String(value); } } }
    );
    assert.strictEqual(out, 'Infinity -Infinity');
  });

  it('keeps a very large integer in string-parameter mode working', function() {
    const template = Handlebars.compile('{{echo ' + huge + '}}', {
      stringParams: true
    });
    const out = template(
      {},
      { helpers: { echo: function(value) { return String(value); } } }
    );
    assert.strictEqual(out, 'Infinity');
  });
});
