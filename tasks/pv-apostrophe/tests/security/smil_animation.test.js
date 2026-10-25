// Security: values that a browser later copies into a live URL attribute must
// not survive sanitization with a scheme the configuration forbids.
//
// Every check drives the library's public entry point and asserts the blocked
// outcome (the forbidden destination is gone) plus a positive control (the
// surrounding legitimate content still survives).
const assert = require('assert');

const PRODUCT = process.env.SANITIZE_HTML_PRODUCT ||
  '/workspace/packages/sanitize-html/index.js';
const sanitizeHtml = require(PRODUCT);

// The library's documented default set of attributes subject to the scheme
// policy, spelled out here so the test does not read product constants.
const SCHEME_CHECKED_ATTRIBUTES = [
  'href', 'src', 'cite',
  'action', 'formaction', 'data', 'xlink:href',
  'poster', 'background', 'ping',
  'longdesc', 'usemap', 'codebase', 'classid', 'archive',
  'profile', 'manifest', 'itemid',
  'dynsrc', 'lowsrc'
];

function animationOptions(extra) {
  return Object.assign({
    allowedTags: [ 'svg', 'a', 'text', 'animate', 'set', 'image' ],
    allowedAttributes: {
      a: [ 'href', 'xlink:href' ],
      text: [ 'y' ],
      animate: [ 'attributename', 'values', 'from', 'to', 'by', 'dur', 'fill' ],
      set: [ 'attributename', 'to', 'dur', 'fill' ],
      image: [ 'src', 'href' ]
    }
  }, extra || {});
}

function assertNoJavascript(out) {
  assert.ok(!/javascript\s*:/i.test(out),
    'a forbidden destination survived sanitization: ' + out);
}

describe('SVG animation retargeting a URL attribute', function() {
  it('drops a values list that smuggles a forbidden scheme after a safe fragment', function() {
    const out = sanitizeHtml(
      '<svg><a><animate attributeName="href" values="#safe;javascript:alert(1)" dur=".01s" fill="freeze"></animate><text y="30">Click me</text></a></svg>',
      animationOptions({
        allowedSchemesAppliedToAttributes: SCHEME_CHECKED_ATTRIBUTES.concat([ 'values' ])
      })
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('Click me') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops a values list with a forbidden scheme when values is not scheme-checked', function() {
    const out = sanitizeHtml(
      '<svg><a><animate attributeName="href" values="javascript:alert(1)" dur=".01s" fill="freeze"></animate><text y="30">Click me</text></a></svg>',
      animationOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('Click me') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops an animation that retargets a link through from', function() {
    const out = sanitizeHtml(
      '<svg><a><animate attributeName="href" from="javascript:alert(1)" to="#safe" dur="1s"></animate><text>x</text></a></svg>',
      animationOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('x') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops a set element that retargets a link through to', function() {
    const out = sanitizeHtml(
      '<svg><a href="#safe"><set attributeName="href" to="javascript:alert(1)" fill="freeze"></set><text>x</text></a></svg>',
      animationOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('x') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops an animation that retargets a link through by', function() {
    const out = sanitizeHtml(
      '<svg><a><animate attributeName="href" by="javascript:alert(1)" dur="1s"></animate><text>x</text></a></svg>',
      animationOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('x') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops an animation that retargets the prefixed form of the link attribute', function() {
    const out = sanitizeHtml(
      '<svg><a xlink:href="#safe"><animate attributeName="xlink:href" values="#safe;javascript:alert(1)" dur="1s"></animate><text>x</text></a></svg>',
      animationOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('x') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops an animation whose target is written in another case or with whitespace', function() {
    const out = sanitizeHtml(
      '<svg><a><animate attributeName=" HREF " values="#safe;javascript:alert(1)" dur="1s"></animate><text>x</text></a></svg>',
      animationOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('x') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops an animation that retargets any other scheme-checked attribute', function() {
    const out = sanitizeHtml(
      '<svg><image><animate attributeName="src" to="javascript:alert(1)" dur="1s"></animate></image></svg>',
      {
        allowedTags: [ 'svg', 'image', 'animate' ],
        allowedAttributes: {
          image: [ 'src' ],
          animate: [ 'attributename', 'to', 'dur' ]
        }
      }
    );
    assertNoJavascript(out);
  });

  it('drops retargeting animations of every SMIL animation element', function() {
    const out = sanitizeHtml(
      '<svg><a>' +
        '<animateColor attributeName="href" values="javascript:alert(1)" dur="1s"></animateColor>' +
        '<animateMotion attributeName="href" to="javascript:alert(1)" dur="1s"></animateMotion>' +
        '<animateTransform attributeName="href" by="javascript:alert(1)" dur="1s"></animateTransform>' +
        '<text>x</text></a></svg>',
      {
        allowedTags: [ 'svg', 'a', 'text', 'animateColor', 'animateMotion', 'animateTransform' ],
        allowedAttributes: {
          a: [ 'href' ],
          text: [ 'y' ],
          animateColor: [ 'attributename', 'values', 'dur' ],
          animateMotion: [ 'attributename', 'to', 'dur' ],
          animateTransform: [ 'attributename', 'by', 'dur' ]
        }
      }
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('x') !== -1, 'legitimate content was lost: ' + out);
  });
});
