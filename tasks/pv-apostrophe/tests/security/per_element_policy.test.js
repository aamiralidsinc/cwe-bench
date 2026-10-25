// Security: where the configuration names a scheme policy for one element, that
// policy is the complete policy for the element. The global list must not widen
// it, including for destinations the browser loads on its own.
const assert = require('assert');

const PRODUCT = process.env.SANITIZE_HTML_PRODUCT ||
  '/workspace/packages/sanitize-html/index.js';
const sanitizeHtml = require(PRODUCT);

describe('per-element scheme policy is complete for its element', function() {
  it('does not let the global list re-admit a scheme the element forbids', function() {
    const out = sanitizeHtml(
      '<iframe src="data:text/html,<script>alert(1)</script>"></iframe><p>keep</p>',
      {
        allowedTags: [ 'iframe', 'p' ],
        allowedAttributes: { iframe: [ 'src' ] },
        allowedSchemes: [ 'https', 'data' ],
        allowedSchemesByTag: { iframe: [ 'https' ] }
      }
    );
    assert.ok(!/data\s*:\s*text\/html/i.test(out),
      'a scheme the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('does not let the global list re-admit a scheme for an ordinary URL attribute', function() {
    const out = sanitizeHtml(
      '<img src="http://policy-violation.invalid/x.png"><p>keep</p>',
      {
        allowedTags: [ 'img', 'p' ],
        allowedAttributes: { img: [ 'src' ] },
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { img: [ 'https' ] }
      }
    );
    assert.ok(out.indexOf('policy-violation.invalid') === -1,
      'a scheme the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('does not let the global list re-admit a scheme inside a list value', function() {
    const out = sanitizeHtml(
      '<img srcset="http://policy-violation.invalid/x.png 1x"><p>keep</p>',
      {
        allowedTags: [ 'img', 'p' ],
        allowedAttributes: { img: [ 'srcset' ] },
        allowedSchemes: [ 'http', 'https' ],
        allowedSchemesByTag: { img: [ 'https' ] }
      }
    );
    assert.ok(out.indexOf('policy-violation.invalid') === -1,
      'a scheme the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });
});
