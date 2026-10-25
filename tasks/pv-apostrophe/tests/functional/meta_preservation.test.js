// Functional: content the policy permits, and content the policy does not
// govern, must be preserved exactly as today.
const assert = require('assert');

const PRODUCT = process.env.SANITIZE_HTML_PRODUCT ||
  '/workspace/packages/sanitize-html/index.js';
const sanitizeHtml = require(PRODUCT);

function metaOptions(extra) {
  return Object.assign({
    allowedTags: [ 'meta', 'p' ],
    allowedAttributes: { meta: [ 'http-equiv', 'content', 'name' ] }
  }, extra || {});
}

describe('permitted and ungoverned meta content keeps working', function() {
  it('keeps a refresh with a permitted destination', function() {
    const content = '0;url=https://example.com/';
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="' + content + '">',
      metaOptions()
    );
    assert.ok(out.indexOf(content) !== -1, 'a permitted refresh was removed: ' + out);
  });

  it('keeps a quoted refresh with a permitted destination', function() {
    const content = "0; URL='https://example.com/'";
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="' + content + '">',
      metaOptions()
    );
    assert.ok(out.indexOf(content) !== -1, 'a permitted refresh was removed: ' + out);
  });

  it('keeps a relative refresh destination', function() {
    const content = '0;url=/relative/path';
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="' + content + '">',
      metaOptions()
    );
    assert.ok(out.indexOf(content) !== -1, 'a permitted refresh was removed: ' + out);
  });

  it('keeps a refresh that has no destination', function() {
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="5">',
      metaOptions()
    );
    assert.ok(out.indexOf('content="5"') !== -1, 'a destination-free refresh was removed: ' + out);
  });

  it('keeps meta content that is not a navigation', function() {
    const out = sanitizeHtml(
      '<meta name="description" content="A price: 5 dollars">',
      metaOptions()
    );
    assert.ok(out.indexOf('A price: 5 dollars') !== -1, 'ordinary meta content was removed: ' + out);
  });

  it('keeps a permitted destination under a narrower per-element policy', function() {
    const content = '0;url=https://example.com/';
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="' + content + '">',
      metaOptions({ allowedSchemesByTag: { meta: [ 'https' ] } })
    );
    assert.ok(out.indexOf(content) !== -1, 'a permitted refresh was removed: ' + out);
  });
});
