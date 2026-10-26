'use strict';
/*
 * Runs one relayed call payload through the platform's own call-notification script inside a
 * small DOM and reports the heading it would show. stdin: {"frame":{...},"myUsersId":42}
 */
const fs = require('fs');
const vm = require('vm');

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const payload = input.frame || {};
const myUsersId = input.myUsersId;

// Serialise a text node the way a browser's innerHTML does for the characters that matter
// here, so `$('<span>').text(value).html()` yields the escaped string a real page would show.
function escapeTextAsHtml(value) {
  const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return String(value).replace(/[&<>"']/g, (ch) => entities[ch]);
}

function jq() {
  // Older jQuery-style text/html semantics: both setters chain, both getters return a value.
  let content = '';
  let contentIsMarkup = false;
  const o = {
    length: 0,
    each() { return o; }, find() { return o; },
    text(value) {
      if (arguments.length === 0) {
        return contentIsMarkup ? String(content).replace(/<[^>]*>/g, '') : content;
      }
      content = String(value);
      contentIsMarkup = false;
      return o;
    },
    html(value) {
      if (arguments.length === 0) {
        return contentIsMarkup ? content : escapeTextAsHtml(content);
      }
      content = String(value);
      contentIsMarkup = true;
      return o;
    },
    remove() { return o; }, attr() { return ''; }, data() { return undefined; },
    addClass() { return o; }, removeClass() { return o; }, hide() { return o; },
    show() { return o; }, ready() { return o; }, get() { return o; },
  };
  // The DOM-level views of the same content, so an escape built from the element's own
  // textContent/innerHTML behaves the way it would in a page.
  Object.defineProperty(o, 'textContent', {
    get() { return contentIsMarkup ? String(content).replace(/<[^>]*>/g, '') : content; },
    set(value) { content = String(value); contentIsMarkup = false; },
  });
  Object.defineProperty(o, 'innerHTML', {
    get() { return contentIsMarkup ? content : escapeTextAsHtml(content); },
    set(value) { content = String(value); contentIsMarkup = true; },
  });
  return o;
}
jq.toast = function (options) {
  sandbox.__heading = options && options.heading;
  sandbox.__toastText = options && options.text;
  return {};
};

const sandbox = {
  console: { log() {}, error() {}, warn() {}, debug() {} },
  setTimeout() { return 0; }, clearTimeout() {}, setInterval() { return 0; }, clearInterval() {},
  JSON, Object, Array, String, Number, Boolean, Math, Date, RegExp, Error,
  parseInt, parseFloat, encodeURIComponent, decodeURIComponent,
  my_users_id: myUsersId,
  socketResourceId: 1,
  webSiteRootURL: 'http://127.0.0.1:9/',
  callerToast: [],
  callingTimeoutSeconds: 30,
  callStartedHere: false,
  users_id: 0,
  setCallBodyClass() {}, avideoToastInfo() {}, avideoToastError() {},
  avideoToastSuccess() {}, avideoToastWarning() {}, avideoModalIframeFull() {},
  isUserOnline() { return true; },
  shouldHangUpCall: 0,
  finishCall() {},
  $: jq,
  jQuery: jq,
  document: { querySelector() { return null; }, querySelectorAll() { return []; }, createElement() { return jq(); } },
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;

const ctx = vm.createContext(sandbox);
const src = fs.readFileSync(process.env.CALLER_SCRIPT || '/workspace/plugin/WebRTC/call/caller.js', 'utf8');
vm.runInContext(src, ctx, { filename: 'caller.js' });

let error = null;
try {
  sandbox.incomeCall(payload);
} catch (e) {
  error = String((e && e.message) || e);
}

process.stdout.write(JSON.stringify({
  heading: typeof sandbox.__heading === 'undefined' ? null : sandbox.__heading,
  imageAndButton: typeof sandbox.__toastText === 'undefined' ? null : sandbox.__toastText,
  error: error,
}));
