'use strict';
/*
 * Runs one frame through the platform's own client socket script inside a small DOM and
 * reports what the browser side actually did. stdin: {"mode":"message"|"response","frame":{...}}
 */
const fs = require('fs');
const vm = require('vm');

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const mode = input.mode === 'response' ? 'response' : 'message';
const frame = input.frame;

function jq() {
  const o = {
    length: 0,
    each() { return o; }, find() { return o; }, text() { return o; }, html() { return o; },
    remove() { return o; }, attr() { return ''; }, data() { return undefined; },
    addClass() { return o; }, removeClass() { return o; }, hide() { return o; },
    parent() { return o; }, on() { return o; }, val() { return ''; }, append() { return o; },
    prepend() { return o; }, css() { return o; }, prop() { return o; }, is() { return false; },
    trigger() { return o; }, slideUp() { return o; }, show() { return o; }, ready() { return o; },
  };
  return o;
}

const sandbox = {
  console: { log() {}, error() {}, warn() {}, debug() {} },
  setTimeout(fn) {
    if (typeof fn === 'string') { vm.runInContext(fn, ctx); }
    else if (typeof fn === 'function') { fn(); }
    return 0;
  },
  clearTimeout() {}, setInterval() { return 0; }, clearInterval() {},
  JSON, Object, Array, String, Number, Boolean, Math, Date, RegExp, Error,
  parseInt, parseFloat, encodeURIComponent, decodeURIComponent,
  fetch: () => Promise.reject(new Error('offline')),
  isOnline: () => true,
  empty: (v) => v === undefined || v === null || v === '' || (Array.isArray(v) && v.length === 0),
  updateSocketUserCard: function () {},
  setCallBodyClass: function () {},
  isUserOnline: function () { return true; },
  avideoToastInfo: function () {}, avideoToastError: function () {}, avideoToastSuccess: function () {},
  avideoToastWarning: function () {},
  webSocketURL: 'ws://127.0.0.1:9',
  webSiteRootURL: 'http://127.0.0.1:9/',
  webSocketServerVersion: 99,
  webSocketTypes: {
    MSG_TO_ALL_LOGGED: 'MSG_TO_ALL_LOGGED', MSG_TO_ALL: 'MSG_TO_ALL',
    OPEN_CONNECTION: 'OPEN_CONNECTION', NEW_CONNECTION: 'NEW_CONNECTION',
    NEW_DISCONNECTION: 'NEW_DISCONNECTION', DEFAULT_MESSAGE: 'DEFAULT_MESSAGE',
    ON_VIDEO_MSG: 'ON_VIDEO_MSG', ON_LIVE_MSG: 'ON_LIVE_MSG', TESTING: 'TESTING',
    UNDEFINED: 'UNDEFINED', MSG_BATCH: 'MSG_BATCH',
  },
  document: {
    dispatchEvent: function (e) { (sandbox.__events || (sandbox.__events = [])).push(e && e.type); },
    querySelector: function () { return null; },
    querySelectorAll: function () { return []; },
    getElementById: function () { return null; },
    find: function () { return jq(); },
    ready: function () {},
  },
  CustomEvent: function (type, opts) { this.type = type; this.detail = opts && opts.detail; },
  $: jq,
  jQuery: jq,
  __callbackCalls: [],
};
// A function name the application itself registers for call notifications.
sandbox.incomeCall = function (details) { sandbox.__callbackCalls.push(details); };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;

const ctx = vm.createContext(sandbox);
// In a browser the timer functions are built in. Report them the way a browser does, so the
// page's own "is this a built-in?" logic sees what it would see in a real page; the string form
// still runs the string, as a browser timer does.
sandbox.__builtins = [sandbox.setTimeout, sandbox.clearTimeout, sandbox.setInterval, sandbox.clearInterval];
vm.runInContext(`(function () {
  var original = Function.prototype.toString;
  Function.prototype.toString = function () {
    if (globalThis.__builtins.indexOf(this) !== -1) {
      return 'function () { [native code] }';
    }
    return original.call(this);
  };
})();`, ctx);
const src = fs.readFileSync(process.env.SOCKET_SCRIPT || '/workspace/plugin/YPTSocket/script.js', 'utf8');
vm.runInContext(src, ctx, { filename: 'script.js' });

let error = null;
try {
  if (mode === 'response') {
    sandbox.yptSocketResponse = frame;
    const p = sandbox.parseSocketResponse();
    if (p && typeof p.catch === 'function') { p.catch(function () {}); }
  } else {
    sandbox.processSocketJson(frame);
  }
} catch (e) {
  error = String((e && e.message) || e);
}

process.stdout.write(JSON.stringify({
  pwned: sandbox.__pwned === 1,
  uiEffect: typeof sandbox.__uiEffect === 'undefined' ? null : sandbox.__uiEffect,
  callbackCalls: sandbox.__callbackCalls.length,
  events: sandbox.__events || [],
  error: error,
}));
