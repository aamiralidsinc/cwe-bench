// Functional: ordinary URL handling, per-element scheme overrides, and list
// values the policy permits must behave exactly as they do today.
const assert = require('assert');

const PRODUCT = process.env.SANITIZE_HTML_PRODUCT ||
  '/workspace/packages/sanitize-html/index.js';
const sanitizeHtml = require(PRODUCT);

describe('ordinary URL policy behaviour is unchanged', function() {
  it('keeps permitted and relative links', function() {
    const out = sanitizeHtml(
      '<a href="https://example.com/page">https</a>' +
      '<a href="mailto:someone@example.com">mail</a>' +
      '<a href="ftp://files.example.com/x">ftp</a>' +
      '<a href="/relative/path">relative</a>',
      { allowedTags: [ 'a' ], allowedAttributes: { a: [ 'href' ] } }
    );
    assert.ok(out.indexOf('href="https://example.com/page"') !== -1, 'https link lost: ' + out);
    assert.ok(out.indexOf('href="mailto:someone@example.com"') !== -1, 'mailto link lost: ' + out);
    assert.ok(out.indexOf('href="ftp://files.example.com/x"') !== -1, 'ftp link lost: ' + out);
    assert.ok(out.indexOf('href="/relative/path"') !== -1, 'relative link lost: ' + out);
  });

  it('keeps the documented per-element override for a direct attribute', function() {
    const out = sanitizeHtml(
      '<img src="https://cdn.invalid/one.png">',
      {
        allowedTags: [ 'img' ],
        allowedAttributes: { img: [ 'src' ] },
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { img: [ 'https' ] }
      }
    );
    assert.ok(out.indexOf('src="https://cdn.invalid/one.png"') !== -1,
      'a destination the per-element policy permits was removed: ' + out);
  });

  it('keeps a permitted data URL under the documented per-element override', function() {
    const data = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==';
    const out = sanitizeHtml(
      '<img src="' + data + '">',
      {
        allowedTags: [ 'img' ],
        allowedAttributes: { img: [ 'src' ] },
        allowedSchemes: [ 'http' ],
        allowedSchemesByTag: { img: [ 'data' ] }
      }
    );
    assert.ok(out.indexOf(data) !== -1, 'a permitted data URL was removed: ' + out);
  });

  it('keeps several permitted destinations in one document', function() {
    const out = sanitizeHtml(
      '<a href="https://one.example/">one</a><a href="https://two.example/">two</a>' +
      '<img src="https://three.example/x.png">',
      {
        allowedTags: [ 'a', 'img' ],
        allowedAttributes: { a: [ 'href' ], img: [ 'src' ] }
      }
    );
    assert.ok(out.indexOf('https://one.example/') !== -1, 'first link lost: ' + out);
    assert.ok(out.indexOf('https://two.example/') !== -1, 'second link lost: ' + out);
    assert.ok(out.indexOf('https://three.example/x.png') !== -1, 'image source lost: ' + out);
  });

  it('keeps protocol-relative URLs when they are permitted', function() {
    const out = sanitizeHtml(
      '<a href="//example.com/x">x</a>',
      { allowedTags: [ 'a' ], allowedAttributes: { a: [ 'href' ] } }
    );
    assert.ok(out.indexOf('href="//example.com/x"') !== -1, 'a permitted URL was removed: ' + out);
  });

  it('drops protocol-relative URLs when they are forbidden', function() {
    const out = sanitizeHtml(
      '<a href="//example.com/x">x</a>',
      {
        allowedTags: [ 'a' ],
        allowedAttributes: { a: [ 'href' ] },
        allowProtocolRelative: false
      }
    );
    assert.ok(out.indexOf('example.com') === -1, 'a forbidden URL survived: ' + out);
  });

  it('keeps permitted list destinations', function() {
    const out = sanitizeHtml(
      '<img srcset="https://cdn.invalid/one.jpg 1x, //cdn.invalid/two.jpg 2x">',
      {
        allowedTags: [ 'img' ],
        allowedAttributes: { img: [ 'srcset' ] },
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { img: [ 'https' ] }
      }
    );
    assert.ok(out.indexOf('https://cdn.invalid/one.jpg') !== -1, 'a permitted list entry was lost: ' + out);
    assert.ok(out.indexOf('//cdn.invalid/two.jpg') !== -1, 'a permitted relative list entry was lost: ' + out);
  });
});
