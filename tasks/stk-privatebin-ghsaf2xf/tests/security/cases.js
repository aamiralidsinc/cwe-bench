'use strict';

/*
 * Security cases. Each one opens a crafted paste through the application's own decryption and
 * display path (or the editor preview tab) and asserts that the attacker-supplied content is not
 * handed to the browser as a document. The markers are inert strings; nothing is executed.
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

const PNG_BYTES = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 1, 2, 3, 4];
const PDF_BYTES = '%PDF-1.4\nMARKER-PDF-7f3a\n%%EOF\n';

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

function downloadLinkCases(harness) {
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
      name: 'T4-v1-html-download-link',
      run: () => withEnv(harness, async env => {
        await env.openV1({
          paste: 'legacy paste',
          attachment: dataUri('text/html', HTML_PAYLOAD),
          name: 'legacy.html'
        });
        await env.waitForHref();
        const hrefType = env.hrefMediaType();
        assert(hrefType !== null, 'the legacy attachment link has no target');
        assert(
          !isActiveDocumentType(hrefType),
          'the legacy attachment link hands the browser content declared as ' + hrefType
        );
      })
    }
  ];
}

function downloadOfferCases(harness) {
  const { dataUri } = harness;

  function unnamedCase(id, mimeType, payload) {
    return {
      name: id,
      run: () => withEnv(harness, async env => {
        await env.openV2({
          paste: 'paste-' + id,
          attachment: dataUri(mimeType, payload),
          attachment_name: null
        });
        await env.waitForHref();
        assert(
          typeof env.downloadAttr() === 'string',
          'the attachment link does not offer the file as a save when the paste carries no name'
        );
      })
    };
  }

  return [
    unnamedCase('T2-v2-unnamed-image-downloads', 'image/png', PNG_BYTES),
    unnamedCase('T2-v2-unnamed-pdf-downloads', 'application/pdf', PDF_BYTES)
  ];
}

function previewDispatchCases(harness) {
  const { dataUri } = harness;

  function embeddedCase(id, mimeType, payload) {
    return {
      name: id,
      run: () => withEnv(harness, async env => {
        await env.openV2({
          paste: 'paste-' + id,
          attachment: dataUri(mimeType, payload),
          attachment_name: 'application/pdf'
        });
        await env.waitForHref();
        env.cloneAndPreview('editor preview');
        const containers = env.previewElements('embed, object, iframe');
        assert(
          containers.length === 0,
          'the preview hands attachment content of type ' + mimeType +
          ' to a document container: ' + env.previewHtml()
        );
      })
    };
  }

  return [
    embeddedCase('T3-editor-preview-html-not-embedded', 'text/html', HTML_PAYLOAD),
    embeddedCase('T3-editor-preview-xhtml-not-embedded', 'application/xhtml+xml', XHTML_PAYLOAD)
  ];
}

function svgPreviewCase(harness) {
  const { dataUri } = harness;
  return {
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
        // nothing is rendered, so there is nothing to run
        return;
      }
      const record = env.recordFor(img.getAttribute('src'));
      if (!record || !/^image\/svg\+xml/i.test(String(record.type))) {
        // the browser is not asked to treat this blob as SVG
        return;
      }
      const text = await env.readBlobText(record.blob);
      assert(
        text.indexOf('__privatebin_marker') === -1 && !/<script/i.test(text),
        'the SVG preview still carries executable script'
      );
    })
  };
}

module.exports = function (harness) {
  return [].concat(
    downloadLinkCases(harness),
    downloadOfferCases(harness),
    previewDispatchCases(harness),
    [svgPreviewCase(harness)]
  );
};
