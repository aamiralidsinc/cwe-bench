// Functional: the sanitizer must keep doing everything it does today for
// animations that are not link retargeting and for content the policy permits.
const assert = require('assert');

const PRODUCT = process.env.SANITIZE_HTML_PRODUCT ||
  '/workspace/packages/sanitize-html/index.js';
const sanitizeHtml = require(PRODUCT);

function animationOptions(extra) {
  return Object.assign({
    allowedTags: [ 'svg', 'a', 'text', 'animate', 'set' ],
    allowedAttributes: {
      a: [ 'href', 'xlink:href', 'attributename' ],
      text: [ 'y' ],
      animate: [ 'attributename', 'values', 'from', 'to', 'by', 'dur', 'fill' ],
      set: [ 'attributename', 'to', 'dur', 'fill' ]
    }
  }, extra || {});
}

describe('animations of values that are not destinations keep working', function() {
  it('keeps an animation of a presentation value', function() {
    const out = sanitizeHtml(
      '<svg><a><animate attributeName="fill" values="red;blue" dur="1s"></animate><text>x</text></a></svg>',
      animationOptions()
    );
    assert.ok(out.indexOf('animate') !== -1, 'the animation was removed: ' + out);
    assert.ok(out.indexOf('red;blue') !== -1, 'the animated values were lost: ' + out);
    assert.ok(out.indexOf('attributename="fill"') !== -1, 'the animation target was lost: ' + out);
  });

  it('keeps a set element targeting a harmless attribute', function() {
    const out = sanitizeHtml(
      '<svg><a><set attributeName="opacity" to="0" dur="1s"></set><text>x</text></a></svg>',
      animationOptions()
    );
    assert.ok(out.indexOf('<set') !== -1, 'the set element was removed: ' + out);
    assert.ok(out.indexOf('to="0"') !== -1, 'the set value was lost: ' + out);
    assert.ok(out.indexOf('attributename="opacity"') !== -1, 'the set target was lost: ' + out);
  });

  it('keeps the href of a non-animation element that also carries a target name', function() {
    const out = sanitizeHtml(
      '<svg><a href="#safe" attributeName="href"><text>x</text></a></svg>',
      animationOptions()
    );
    assert.ok(out.indexOf('href="#safe"') !== -1, 'a permitted link was removed: ' + out);
    assert.ok(out.indexOf('attributename="href"') !== -1, 'an ordinary attribute was removed: ' + out);
  });

  it('keeps ordinary content and permitted links around an animation', function() {
    const out = sanitizeHtml(
      '<svg><a href="https://example.com/page"><animate attributeName="fill" values="red;blue" dur="1s"></animate><text y="30">Click me</text></a></svg>',
      animationOptions()
    );
    assert.ok(out.indexOf('href="https://example.com/page"') !== -1, 'a permitted link was removed: ' + out);
    assert.ok(out.indexOf('Click me') !== -1, 'legitimate content was lost: ' + out);
  });
});
