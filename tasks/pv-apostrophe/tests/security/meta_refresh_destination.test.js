// Security: a destination the browser navigates to from a value it parses
// itself must not carry a scheme the configuration forbids.
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

function assertNoJavascript(out) {
  assert.ok(!/javascript\s*:/i.test(out),
    'a forbidden destination survived sanitization: ' + out);
}

describe('navigation destinations embedded in a value the browser parses', function() {
  it('drops a refresh destination with a forbidden scheme', function() {
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="0;url=javascript:alert(1)"><p>keep</p>',
      metaOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops a refresh destination using a scheme outside the allowed set', function() {
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="0;url=data:text/html,<script>alert(1)</script>"><p>keep</p>',
      metaOptions()
    );
    assert.ok(!/data\s*:\s*text\/html/i.test(out),
      'a forbidden destination survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('drops refresh destinations across separators, quoting, spelling and case', function() {
    const contents = [
      '0;URL=javascript:alert(1)',
      '0; url = javascript:alert(1)',
      '0,url=javascript:alert(1)',
      '0 url=javascript:alert(1)',
      '  1.5 ;  Url=JavaScript:alert(1)',
      '.5;url=javascript:alert(1)',
      '0;url="javascript:alert(1)"',
      "0;url='javascript:alert(1)'",
      '0;javascript:alert(1)',
      '0;"javascript:alert(1)"'
    ];
    contents.forEach(function(content) {
      const html = '<meta http-equiv="refresh" content="' +
        content.replace(/"/g, '&quot;') + '"><p>keep</p>';
      const out = sanitizeHtml(html, metaOptions());
      assertNoJavascript(out);
      assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost for ' + content + ': ' + out);
    });
  });

  it('applies the same rule when the refresh marker is written in another case and order', function() {
    const out = sanitizeHtml(
      '<meta content="0;url=javascript:alert(1)" HTTP-EQUIV="Refresh"><p>keep</p>',
      metaOptions()
    );
    assertNoJavascript(out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });

  it('honours the per-element scheme policy for an embedded destination', function() {
    const out = sanitizeHtml(
      '<meta http-equiv="refresh" content="0;url=http://policy-violation.invalid/x"><p>keep</p>',
      metaOptions({ allowedSchemesByTag: { meta: [ 'https' ] } })
    );
    assert.ok(out.indexOf('policy-violation.invalid') === -1,
      'a destination the per-element policy forbids survived sanitization: ' + out);
    assert.ok(out.indexOf('keep') !== -1, 'legitimate content was lost: ' + out);
  });
});
