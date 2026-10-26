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

// HTML-escape a string the way a text node serialised through innerHTML would: the characters
// that change meaning in markup are replaced, so "$('<span>').text(x).html()" yields escaped text.
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// The text a browser would extract from markup (tags dropped, basic entities decoded).
function markupToText(value) {
  return String(value)
    .replace(/<[^>]*>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&');
}

function jq() {
  let content = null;            // last value written through text() or html()
  let contentIsMarkup = false;   // whether content came from html(value)
  const o = {
    length: 0,
    each() { return o; }, find() { return o; },
    // text(value) stores text and chains; text() reads it back.
    text(value) {
      if (arguments.length === 0) {
        if (content === null) { return ''; }
        return contentIsMarkup ? markupToText(content) : content;
      }
      content = value === null || typeof value === 'undefined' ? '' : String(value);
      contentIsMarkup = false;
      return o;
    },
    // html(value) stores markup and chains; html() returns the content as a string, escaping
    // text that was set as text.
    html(value) {
      if (arguments.length === 0) {
        if (content === null) { return ''; }
        return contentIsMarkup ? content : escapeHtml(content);
      }
      content = value === null || typeof value === 'undefined' ? '' : String(value);
      contentIsMarkup = true;
      return o;
    },
    remove() { return o; }, attr() { return ''; }, data() { return undefined; },
    addClass() { return o; }, removeClass() { return o; }, hide() { return o; },
    show() { return o; }, ready() { return o; },
  };
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
