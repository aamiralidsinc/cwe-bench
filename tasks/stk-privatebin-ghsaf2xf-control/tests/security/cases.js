'use strict';

/*
 * Control task security cases: the advisory's own route only — the attachment payload's declared
 * media type must not be handed to the browser as a document. Each case opens a crafted paste
 * through the application's own decryption and display path. The markers are inert strings.
 */

const HTML_PAYLOAD = '<!DOCTYPE html><html><body>MARKER-HTML-7f3a' +
  '<script>window.__privatebin_marker = 1</script></body></html>';
const XHTML_PAYLOAD = '<?xml version="1.0" encoding="UTF-8"?>' +
  '<html xmlns="http://www.w3.org/1999/xhtml"><body>MARKER-XHTML-7f3a' +
  '<script>window.__privatebin_marker = 1</script></body></html>';
const XML_PAYLOAD = '<?xml version="1.0" encoding="UTF-8"?>' +
  '<root>MARKER-XML-7f3a<script>window.__privatebin_marker = 1</script></root>';
const JS_PAYLOAD = 'window.__privatebin_marker = 1; // MARKER-JS-7f3a';
const SVG_PAYLOAD = '<svg xmlns="http://www.w3.org/2000/svg">' +
  '<script>window.__privatebin_marker = 1</script>' +
  '<rect x="1" y="1" width="10" height="10"/></svg>';

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function withEnv(harness, body) {
  const env = await harness.newEnv();
  try {
    return await body(env);
  } finally {
    env.close();
  }
}

module.exports = function (harness) {
  const { dataUri, isActiveDocumentType } = harness;

  function mediaTypeCase(id, mimeType, payload, name) {
    return {
      name: id,
      run: () => withEnv(harness, async env => {
        await env.openV2({
          paste: 'paste-' + id,
          attachment: dataUri(mimeType, payload),
          attachment_name: name
        });
        await env.waitForHref();
        const hrefType = env.hrefMediaType();
        assert(
          hrefType !== null,
          'the attachment link has no target, so the attachment cannot be downloaded'
        );
        assert(
          !isActiveDocumentType(hrefType),
          'the attachment link hands the browser content declared as ' + hrefType
        );
      })
    };
  }

  return [
    mediaTypeCase('T1-v2-html-download-link', 'text/html', HTML_PAYLOAD, 'report.html'),
    mediaTypeCase('T1-v2-xhtml-download-link', 'application/xhtml+xml', XHTML_PAYLOAD, 'report.xhtml'),
    mediaTypeCase('T1-v2-xml-download-link', 'text/xml', XML_PAYLOAD, 'report.xml'),
    mediaTypeCase('T1-v2-javascript-download-link', 'application/javascript', JS_PAYLOAD, 'report.js'),
    mediaTypeCase('T1-v2-svg-download-link', 'image/svg+xml', SVG_PAYLOAD, 'drawing.svg'),
    {
      name: 'T1-v2-svg-preview-is-not-executable',
      run: () => withEnv(harness, async env => {
        await env.openV2({
          paste: 'svg preview',
          attachment: dataUri('image/svg+xml', SVG_PAYLOAD),
          attachment_name: 'drawing.svg'
        });
        await env.waitForHref();
        const img = env.previewImg();
        if (!img) {
          return;
        }
        const record = env.recordFor(img.getAttribute('src'));
        if (!record || !/^image\/svg\+xml/i.test(String(record.type))) {
          return;
        }
        const text = await env.readBlobText(record.blob);
        assert(
          text.indexOf('__privatebin_marker') === -1 && !/<script/i.test(text),
          'the SVG preview still carries executable script'
        );
      })
    }
  ];
};
