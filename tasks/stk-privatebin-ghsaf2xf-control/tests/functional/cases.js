'use strict';

/*
 * Functional cases. These describe behaviour that works at the pinned commit and must keep
 * working: previews, exact download names, original attachment content, the legacy route, and the
 * editor preview tab. Every expected value is a literal in the case.
 */

const HTML_PAYLOAD = '<!DOCTYPE html><html><body>MARKER-HTML-7f3a' +
  '<script>window.__privatebin_marker = 1</script></body></html>';
const SVG_PAYLOAD = '<svg xmlns="http://www.w3.org/2000/svg">' +
  '<rect x="1" y="1" width="10" height="10"/></svg>';
const PNG_BYTES = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 1, 2, 3, 4];
const PDF_BYTES = '%PDF-1.4\nMARKER-PDF-7f3a\n%%EOF\n';

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function sameBytes(a, b) {
  if (a.length !== b.length) { return false; }
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) { return false; }
  }
  return true;
}

async function withEnv(harness, body) {
  const env = await harness.newEnv();
  try {
    return await body(env);
  } finally {
    env.close();
  }
}

function previewCases(harness) {
  const { dataUri } = harness;

  const cases = [];

  cases.push({
    name: 'F-image-preview-and-content',
    run: () => withEnv(harness, async env => {
      await env.openV2({
        paste: 'image paste',
        attachment: dataUri('image/png', PNG_BYTES),
        attachment_name: 'photo.png'
      });
      await env.waitForHref();
      assert(env.hrefMediaType() === 'image/png', 'the image lost its media type');
      assert(env.downloadAttr() === 'photo.png', 'the download name changed');
      const img = env.previewImg();
      assert(!!img, 'the image preview is gone');
      const record = env.recordFor(img.getAttribute('src'));
      assert(!!record && record.type === 'image/png', 'the preview no longer shows an image');
      const bytes = await env.readBlob(env.attachmentBlob());
      assert(sameBytes(bytes, PNG_BYTES), 'the downloaded attachment content changed');
    })
  });

  cases.push({
    name: 'F-video-preview',
    run: () => withEnv(harness, async env => {
      const payload = [0, 0, 0, 24, 102, 116, 121, 112];
      await env.openV2({
        paste: 'video paste',
        attachment: dataUri('video/mp4', payload),
        attachment_name: 'clip.mp4'
      });
      await env.waitForHref();
      assert(env.hrefMediaType() === 'video/mp4', 'the video lost its media type');
      const source = env.previewElements('video source')[0];
      assert(!!source, 'the video preview is gone');
      const record = env.recordFor(source.getAttribute('src'));
      assert(!!record && record.type === 'video/mp4', 'the preview no longer shows a video');
    })
  });

  cases.push({
    name: 'F-audio-preview',
    run: () => withEnv(harness, async env => {
      const payload = 'ID3MARKER-AUDIO-7f3a';
      await env.openV2({
        paste: 'audio paste',
        attachment: dataUri('audio/mpeg', payload),
        attachment_name: 'sound.mp3'
      });
      await env.waitForHref();
      assert(env.hrefMediaType() === 'audio/mpeg', 'the audio lost its media type');
      const source = env.previewElements('audio source')[0];
      assert(!!source, 'the audio preview is gone');
      const record = env.recordFor(source.getAttribute('src'));
      assert(!!record && record.type === 'audio/mpeg', 'the preview no longer shows audio');
    })
  });

  cases.push({
    name: 'F-pdf-preview',
    run: () => withEnv(harness, async env => {
      await env.openV2({
        paste: 'pdf paste',
        attachment: dataUri('application/pdf', PDF_BYTES),
        attachment_name: 'document.pdf'
      });
      await env.waitForHref();
      assert(env.hrefMediaType() === 'application/pdf', 'the PDF lost its media type');
      const embed = env.previewElements('embed')[0];
      assert(!!embed, 'the PDF preview is gone');
      const record = env.recordFor(embed.getAttribute('src'));
      assert(!!record && record.type === 'application/pdf', 'the preview no longer shows the PDF');
    })
  });

  cases.push({
    name: 'F-svg-preview-available',
    run: () => withEnv(harness, async env => {
      await env.openV2({
        paste: 'svg paste',
        attachment: dataUri('image/svg+xml', SVG_PAYLOAD),
        attachment_name: 'drawing.svg'
      });
      await env.waitForHref();
      const img = env.previewImg();
      assert(!!img, 'the SVG preview is gone');
      const record = env.recordFor(img.getAttribute('src'));
      assert(!!record && record.type === 'image/svg+xml', 'the preview no longer shows the SVG');
    })
  });

  return cases;
}

function preservationCases(harness) {
  const { dataUri } = harness;
  return [
    {
      name: 'F-download-content-preserved',
      run: () => withEnv(harness, async env => {
        await env.openV2({
          paste: 'html paste',
          attachment: dataUri('text/html', HTML_PAYLOAD),
          attachment_name: 'report.html'
        });
        await env.waitForHref();
        assert(env.downloadAttr() === 'report.html', 'the download name changed');
        const bytes = await env.readBlob(env.attachmentBlob());
        assert(
          Buffer.from(bytes).toString('utf8') === HTML_PAYLOAD,
          'the downloaded attachment is no longer the file the paste carried'
        );
      })
    },
    {
      name: 'F-legacy-attachment-displays',
      run: () => withEnv(harness, async env => {
        await env.openV1({
          paste: 'legacy paste',
          attachment: dataUri('text/html', HTML_PAYLOAD),
          name: 'legacy.html'
        });
        await env.waitForHref();
        assert(env.downloadAttr() === 'legacy.html', 'the legacy download name changed');
        const bytes = await env.readBlob(env.attachmentBlob());
        assert(
          Buffer.from(bytes).toString('utf8') === HTML_PAYLOAD,
          'the legacy attachment content changed'
        );
      })
    },
    {
      name: 'F-attachment-name-roundtrip',
      run: () => withEnv(harness, async env => {
        const name = 'Zoë "quoted" & <b>tag</b>.png';
        await env.openV2({
          paste: 'name paste',
          attachment: dataUri('image/png', PNG_BYTES),
          attachment_name: name
        });
        await env.waitForHref();
        assert(env.downloadAttr() === name, 'the attachment name was rewritten');
        env.cloneAndPreview('name paste');
        const anchor = env.doc.querySelector('#customattachment a');
        assert(!!anchor, 'the cloned attachment link is gone');
        assert(
          anchor.textContent === "Cloned: '" + name + "'",
          'the attachment name is no longer shown as text: ' + JSON.stringify(anchor.textContent)
        );
        assert(
          anchor.children.length === 0,
          'the attachment name was parsed as markup'
        );
      })
    }
  ];
}

function editorCases(harness) {
  const { dataUri } = harness;
  return [
    {
      name: 'F-editor-preview-shows-image',
      run: () => withEnv(harness, async env => {
        await env.openV2({
          paste: 'editor paste',
          attachment: dataUri('image/png', PNG_BYTES),
          attachment_name: 'image/png'
        });
        await env.waitForHref();
        env.cloneAndPreview('editor paste');
        const img = env.previewImg();
        assert(!!img, 'the editor image preview is gone');
        const record = env.recordFor(img.getAttribute('src'));
        assert(!!record && record.type === 'image/png', 'the editor preview no longer shows the image');
      })
    },
    {
      name: 'F-paste-without-attachment',
      run: () => withEnv(harness, async env => {
        await env.openV2({ paste: 'plain paste' });
        assert(!env.href(), 'an attachment link appeared without an attachment');
        assert(env.attachAreaHidden(), 'the attachment area is shown without an attachment');
      })
    }
  ];
}

function projectBehaviourCases(harness) {
  const { dataUri } = harness;

  const previewVisibility = [
    ['image/png', true],
    ['image/svg+xml', true],
    ['video/mp4', true],
    ['audio/mpeg', true],
    ['application/pdf', true],
    ['text/plain', false],
    ['text/html', false],
    ['application/octet-stream', false]
  ];

  return [
    {
      name: 'F-preview-visibility-by-type',
      run: () => withEnv(harness, async env => {
        for (const [mimeType, expected] of previewVisibility) {
          env.removeAttachment();
          env.setAttachment(dataUri(mimeType, PNG_BYTES), 'file.bin');
          env.showAttachment();
          const visible = !env.previewHidden();
          assert(
            visible === expected,
            mimeType + ': preview visibility changed (expected ' + expected + ')'
          );
        }
        env.removeAttachment();
      })
    },
    {
      name: 'F-attachment-viewer-roundtrip',
      run: () => withEnv(harness, async env => {
        env.setAttachment(dataUri('image/png', PNG_BYTES), 'file name.png');
        const attachment = env.P.AttachmentViewer.getAttachment();
        assert(
          typeof attachment[0] === 'string' && attachment[0].indexOf('blob:') === 0,
          'the attachment link has no blob target'
        );
        assert(attachment[1] === 'file name.png', 'the attachment name changed');
        env.showAttachment();
        assert(!env.attachAreaHidden(), 'the attachment is not shown');
        const container = env.jq(env.doc.createElement('div'));
        env.P.AttachmentViewer.moveAttachmentTo(container, 'Attached: %s');
        const link = container.children()[0];
        assert(!!link, 'the moved attachment link is gone');
        assert(link.getAttribute('download') === 'file name.png', 'the moved download name changed');
        assert(link.textContent === 'Attached: file name.png', 'the attachment label changed');
        env.removeAttachment();
        assert(env.attachAreaHidden(), 'the attachment is not hidden after removal');
      })
    }
  ];
}

module.exports = function (harness) {
  return [].concat(
    previewCases(harness),
    preservationCases(harness),
    editorCases(harness),
    projectBehaviourCases(harness)
  );
};
