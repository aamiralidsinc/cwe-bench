'use strict';

const assert = require('node:assert');
const { Handlebars } = require('../support/product');

describe('preservation: template text', function() {
  it('renders values, escapes them and resolves helpers', function() {
    const template = Handlebars.compile(
      'Hello {{name}}! {{shout word}} {{escaped}}'
    );
    const out = template(
      { name: 'world', word: 'hi', escaped: '<b>&' },
      { helpers: { shout: function(value) { return value.toUpperCase() + '!'; } } }
    );
    assert.strictEqual(out, 'Hello world! HI! &lt;b&gt;&amp;');
  });

  it('renders a partial with the context it is given', function() {
    const template = Handlebars.compile('A{{> part}}B');
    assert.strictEqual(
      template({ name: 'n' }, { partials: { part: '[{{name}}]' } }),
      'A[n]B'
    );
  });

  it('round-trips a prepared template specification', function() {
    const spec = Handlebars.precompile('Hello {{name}}!');
    const template = Handlebars.template(eval('(' + spec + ')'));
    assert.strictEqual(template({ name: 'x' }), 'Hello x!');
  });
});
