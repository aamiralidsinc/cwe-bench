'use strict';

/*
 * Test harness for the PrivateBin task.
 *
 * The product is browser JavaScript. Every environment below creates a fresh jsdom document, loads
 * the application files that the shipped pages load, points the page's object-URL API at a recorder
 * (so a test can see the blob and media type the browser would be handed), and then drives the real
 * application: a crafted encrypted paste is opened through PasteDecrypter.run, or the editor's
 * preview tab is activated. Fixture ciphertext is produced here with Node's crypto and zlib, never
 * with product code, and every expected value in a case is a literal.
 */

const path = require('path');
const nodeCrypto = require('crypto');
const zlib = require('zlib');
const { JSDOM } = require('jsdom');

const PRODUCT_ROOT = process.env.PRODUCT_ROOT || '/workspace';

// The fragment of the page URL is the paste key. '0' is not a base58 character, so the
// application uses this value verbatim instead of base58-decoding it.
const KEY = 'K0' + 'a1b2c3d4e5'.repeat(3);

const PRODUCT_FILES = [
  'jquery-3.6.0.js',
  'rawinflate-0.3.js',
  'showdown-2.0.0.js',
  'purify-2.3.6.js',
  'base-x-4.0.0.js',
  'base64-1.7.js',
  'legacy.js',
  'privatebin.js'
];

const BODY = [
  '<div id="noscript"></div>',
  '<div id="errormessage" class="hidden"><span></span></div>',
  '<div id="loadingindicator" class="hidden"><span></span></div>',
  '<div id="status" class="hidden"><span></span></div>',
  '<div id="remainingtime" class="hidden"></div>',
  '<div id="pastesuccess" class="hidden"></div>',
  '<div id="attachment" role="alert" class="hidden alert alert-info">',
  '<span class="glyphicon glyphicon-download-alt" aria-hidden="true"></span> ',
  '<a class="alert-link">Download attachment</a></div>',
  '<div id="attachmentPreview" class="hidden"></div>',
  '<div id="dragAndDropFileName"></div>',
  '<div id="dropzone" class="hidden"></div>',
  '<input type="file" id="file">',
  '<div id="editorTabs" class="hidden"><ul class="nav nav-tabs">',
  '<li><a id="messageedit" href="#messageedit">edit</a></li>',
  '<li><a id="messagepreview" href="#messagepreview">preview</a></li></ul></div>',
  '<textarea id="message"></textarea>',
  '<div id="placeholder" class="hidden">+++ no paste text +++</div>',
  '<div id="prettymessage" class="hidden"><pre id="prettyprint" class="prettyprint linenums:1"></pre></div>',
  '<div id="plaintext" class="hidden"></div>',
  '<div id="templates"></div>',
  '<div id="attach"></div><div id="customattachment"></div><div id="filewrap"></div>',
  '<input id="passwordinput"><input id="password">',
  '<a id="retrybutton"></a><a id="sendbutton"></a><a id="clonebutton"></a>',
  '<a id="rawtextbutton"></a><a id="downloadtextbutton"></a>',
  '<a id="qrcodelink"></a><a id="emaillink"></a><a id="newbutton"></a>',
  '<a id="fileremovebutton"></a>',
  '<input id="burnafterreading"><input id="burnafterreadingoption">',
  '<input id="opendiscussion"><input id="opendiscussionoption">',
  '<select id="expiration"></select><select id="formatter"></select>',
  '<select id="pasteExpiration"><option value="5min">5min</option></select>',
  '<select id="pasteFormatter"><option value="plaintext">plaintext</option></select>'
].join('');

function b64(value) {
  return Buffer.from(value).toString('base64');
}

function dataUri(mimeType, bytesOrString) {
  const bytes = typeof bytesOrString === 'string'
    ? Buffer.from(bytesOrString, 'utf8')
    : Buffer.from(bytesOrString);
  return 'data:' + mimeType + ';base64,' + bytes.toString('base64');
}

/* Version 2 paste ciphertext: [ciphertext, adata], compression 'none'. */
function makeV2(key, plainObject) {
  const iv = nodeCrypto.randomBytes(16);
  const salt = nodeCrypto.randomBytes(8);
  const spec = [b64(iv), b64(salt), 100000, 256, 128, 'aes', 'gcm', 'none'];
  const adata = [spec, 'plaintext', 0, 0];
  const plaintext = Buffer.from(JSON.stringify(plainObject), 'utf8');
  const derived = nodeCrypto.pbkdf2Sync(Buffer.from(key, 'utf8'), salt, 100000, 32, 'sha256');
  const cipher = nodeCrypto.createCipheriv('aes-256-gcm', derived, iv, { authTagLength: 16 });
  cipher.setAAD(Buffer.from(JSON.stringify(adata), 'utf8'));
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  return {
    ct: b64(Buffer.concat([ciphertext, cipher.getAuthTag()])),
    adata
  };
}

/* Version 1 paste ciphertext: raw deflate of the text, base64 text, then AES-GCM. */
function makeV1(key, plaintext) {
  const iv = nodeCrypto.randomBytes(16);
  const salt = nodeCrypto.randomBytes(8);
  const compressed = zlib.deflateRawSync(Buffer.from(plaintext, 'utf8'));
  const encoded = compressed.toString('base64');
  const derived = nodeCrypto.pbkdf2Sync(Buffer.from(key, 'latin1'), salt, 100000, 32, 'sha256');
  const cipher = nodeCrypto.createCipheriv('aes-256-gcm', derived, iv, { authTagLength: 16 });
  cipher.setAAD(Buffer.from('', 'utf8'));
  const ciphertext = Buffer.concat([
    cipher.update(Buffer.from(encoded, 'latin1')),
    cipher.final()
  ]);
  return JSON.stringify({
    iv: b64(iv), v: 1, iter: 100000, ks: 256, ts: 128, mode: 'gcm',
    adata: '', cipher: 'aes', salt: b64(salt),
    ct: b64(Buffer.concat([ciphertext, cipher.getAuthTag()]))
  });
}

/* Media types a browser may interpret as an active document in the page's origin. */
const ACTIVE_DOCUMENT_TYPES = [
  'text/html',
  'application/xhtml+xml',
  'text/xml',
  'application/xml',
  'application/xml-dtd',
  'image/svg+xml',
  'application/javascript',
  'text/javascript',
  'application/x-javascript'
];

function isActiveDocumentType(mimeType) {
  const base = String(mimeType || '').split(';')[0].trim().toLowerCase();
  return ACTIVE_DOCUMENT_TYPES.indexOf(base) !== -1;
}

function clearProductCache() {
  for (const file of PRODUCT_FILES) {
    try {
      delete require.cache[require.resolve(path.join(PRODUCT_ROOT, 'js', file))];
    } catch (err) {
      // not loaded yet
    }
  }
}

function tick(ms) {
  return new Promise(resolve => setTimeout(resolve, ms === undefined ? 0 : ms));
}

class Env {
  constructor(dom, captured, product) {
    this.dom = dom;
    this.window = dom.window;
    this.doc = dom.window.document;
    this.captured = captured;
    this.P = product;
    this.jq = global.jQuery;
    this.key = this.window.location.hash.substring(1) || KEY;
  }

  close() {
    try { this.window.close(); } catch (err) { /* jsdom teardown */ }
  }

  link() {
    return this.doc.querySelector('#attachment a');
  }

  href() {
    const link = this.link();
    return link ? link.getAttribute('href') : null;
  }

  downloadAttr() {
    const link = this.link();
    return link ? link.getAttribute('download') : null;
  }

  /* The blob record the page's object-URL API returned for a URL. */
  recordFor(url) {
    if (!url) { return null; }
    for (const record of this.captured) {
      if (record.url === url) { return record; }
    }
    return null;
  }

  /* Media type the browser would use for the attachment link's target. */
  hrefMediaType() {
    const href = this.href();
    if (!href) { return null; }
    if (href.indexOf('data:') === 0) {
      const match = /^data:([^;,]*)/.exec(href);
      return match ? match[1] : '';
    }
    const record = this.recordFor(href);
    return record ? record.type : null;
  }

  attachmentBlob() {
    const record = this.recordFor(this.href());
    return record ? record.blob : null;
  }

  previewElements(selector) {
    return Array.prototype.slice.call(
      this.doc.querySelectorAll('#attachmentPreview ' + selector)
    );
  }

  previewHtml() {
    const preview = this.doc.querySelector('#attachmentPreview');
    return preview ? preview.innerHTML : '';
  }

  previewImg() {
    return this.doc.querySelector('#attachmentPreview img');
  }

  async readBlob(blob) {
    return new Promise((resolve, reject) => {
      const reader = new this.window.FileReader();
      reader.onload = () => resolve(new Uint8Array(reader.result));
      reader.onerror = () => reject(reader.error || new Error('could not read blob'));
      reader.readAsArrayBuffer(blob);
    });
  }

  async readBlobText(blob) {
    const bytes = await this.readBlob(blob);
    return Buffer.from(bytes).toString('utf8');
  }

  async waitFor(predicate, timeoutMs) {
    const limit = timeoutMs === undefined ? 5000 : timeoutMs;
    const deadline = Date.now() + limit;
    while (Date.now() < deadline) {
      let value;
      try { value = predicate(); } catch (err) { value = false; }
      if (value) { return value; }
      await tick(20);
    }
    return null;
  }

  async waitForHref(timeoutMs) {
    const found = await this.waitFor(() => this.href(), timeoutMs);
    if (!found) {
      throw new Error('the paste display never produced an attachment link');
    }
    return found;
  }

  async waitForText(text, timeoutMs) {
    const found = await this.waitFor(
      () => this.doc.querySelector('#prettyprint').textContent.indexOf(text) !== -1,
      timeoutMs
    );
    if (!found) {
      throw new Error('the paste text was not displayed');
    }
  }

  /* Open a version-2 paste through the application's decryption and display path. */
  async openV2(plainObject) {
    const fixture = makeV2(KEY, plainObject);
    const paste = this.P.Helper.PasteFactory({
      v: 2, ct: fixture.ct, adata: fixture.adata, meta: {}
    });
    this.P.PasteDecrypter.run(paste);
    await this.waitForText(plainObject.paste);
  }

  /* Open a version-1 paste through the application's decryption and display path. */
  async openV1(legacy) {
    const paste = this.P.Helper.PasteFactory({
      v: 1,
      data: makeV1(KEY, legacy.paste),
      attachment: makeV1(KEY, legacy.attachment),
      attachmentname: makeV1(KEY, legacy.name),
      meta: { formatter: 'plaintext' },
      comments: []
    });
    this.P.PasteDecrypter.run(paste);
    await this.waitForText(legacy.paste);
  }

  /* Clone the shown paste into the editor, then switch to the editor's preview tab. */
  cloneAndPreview(text) {
    this.P.Editor.setText(text === undefined ? 'text' : text);
    this.P.Controller.clonePaste();
    this.jq('#messagepreview').trigger('click');
    return this.previewHtml();
  }

  /* Direct attachment-viewer use, for the preview-visibility and round-trip cases. */
  setAttachment(uri, name) {
    this.P.AttachmentViewer.init();
    if (name === undefined) {
      this.P.AttachmentViewer.setAttachment(uri);
    } else {
      this.P.AttachmentViewer.setAttachment(uri, name);
    }
  }

  showAttachment() {
    this.P.AttachmentViewer.showAttachment();
  }

  attachAreaHidden() {
    const area = this.doc.querySelector('#attachment');
    return !!area && area.classList.contains('hidden');
  }

  previewHidden() {
    const area = this.doc.querySelector('#attachmentPreview');
    return !!area && area.classList.contains('hidden');
  }

  removeAttachment() {
    this.P.AttachmentViewer.removeAttachment();
  }
}

async function newEnv() {
  const dom = new JSDOM(
    '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>' + BODY + '</body></html>',
    { url: 'https://paste.example/', pretendToBeVisual: true }
  );
  const window = dom.window;
  const captured = [];
  let sequence = 0;

  for (const name of [
    'window', 'document', 'navigator', 'location', 'history', 'Blob', 'FileReader',
    'Node', 'HTMLElement', 'XMLHttpRequest', 'URL', 'localStorage', 'sessionStorage'
  ]) {
    global[name] = window[name];
  }
  Object.defineProperty(window, 'crypto', {
    value: nodeCrypto.webcrypto,
    configurable: true
  });
  window.URL.createObjectURL = function (blob) {
    const url = 'blob:https://paste.example/' + (++sequence);
    captured.push({ url: url, type: blob && blob.type, blob: blob });
    return url;
  };
  window.URL.revokeObjectURL = function () {};

  clearProductCache();
  global.jQuery = global.$ = require(path.join(PRODUCT_ROOT, 'js/jquery-3.6.0.js'));
  global.RawDeflate = require(path.join(PRODUCT_ROOT, 'js/rawinflate-0.3.js')).RawDeflate;
  global.showdown = require(path.join(PRODUCT_ROOT, 'js/showdown-2.0.0.js'));
  global.DOMPurify = require(path.join(PRODUCT_ROOT, 'js/purify-2.3.6.js'));
  global.baseX = require(path.join(PRODUCT_ROOT, 'js/base-x-4.0.0.js')).baseX;
  global.Base64 = require(path.join(PRODUCT_ROOT, 'js/base64-1.7.js')).Base64;
  global.Legacy = require(path.join(PRODUCT_ROOT, 'js/legacy.js')).Legacy;
  // The application reads a global zlib interface. These cases never compress, so a resolved
  // placeholder is enough and no WebAssembly fetch is needed.
  global.zlib = Promise.resolve(undefined);
  require(path.join(PRODUCT_ROOT, 'js/privatebin.js'));

  // Let the page's own start-up (DOMContentLoaded handlers) finish before driving the app.
  await tick(0);
  await tick(20);

  const product = global.jQuery.PrivateBin;
  for (const moduleName of [
    'Model', 'Alert', 'PasteStatus', 'Prompt', 'PasteViewer', 'TopNav',
    'AttachmentViewer', 'Editor', 'UiHelper', 'DiscussionViewer'
  ]) {
    if (product[moduleName] && typeof product[moduleName].init === 'function') {
      product[moduleName].init();
    }
  }
  product.Model.init();
  window.location.hash = KEY;

  return new Env(dom, captured, product);
}

module.exports = {
  PRODUCT_ROOT,
  KEY,
  ACTIVE_DOCUMENT_TYPES,
  b64,
  dataUri,
  isActiveDocumentType,
  newEnv
};
