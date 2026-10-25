// Security: the scheme policy that applies to an element must govern every
// destination emitted on that element, including destinations inside a list
// value.
const assert = require('assert');

const PRODUCT = process.env.SANITIZE_HTML_PRODUCT ||
  '/workspace/packages/sanitize-html/index.js';
const sanitizeHtml = require(PRODUCT);

describe('per-element scheme policy over list values', function() {
  it('drops list destinations when the element permits no scheme at all', function() {
    const out = sanitizeHtml(
      '<p>keep</p><img src="https://cdn.invalid/fallback.jpg" srcset="https://cdn.invalid/one.jpg 1x">',
      {
        allowedTags: [ 'p', 'img' ],
        allowedAttributes: { img: [ 'src', 'srcset' ] },
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { img: [] }
      }
    );
    assert.ok(out.indexOf('cdn.invalid') === -1,
      'a destination the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops only the list destinations the per-element policy forbids', function() {
    const out = sanitizeHtml(
      '<p>keep</p><img srcset="http://policy-violation.invalid/bad.jpg 1x, https://cdn.invalid/good.jpg 2x">',
      {
        allowedTags: [ 'p', 'img' ],
        allowedAttributes: { img: [ 'srcset' ] },
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { img: [ 'https' ] }
      }
    );
    assert.ok(out.indexOf('policy-violation.invalid') === -1,
      'a destination the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('applies the per-element policy to the alternate list attribute too', function() {
    const out = sanitizeHtml(
      '<p>keep</p><link rel="preload" as="image" imagesrcset="http://policy-violation.invalid/bad.jpg 1x">',
      {
        allowedTags: [ 'p', 'link' ],
        allowedAttributes: { link: [ 'rel', 'as', 'imagesrcset' ] },
        selfClosing: [ 'link' ],
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { link: [ 'https' ] }
      }
    );
    assert.ok(out.indexOf('policy-violation.invalid') === -1,
      'a destination the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });
});
