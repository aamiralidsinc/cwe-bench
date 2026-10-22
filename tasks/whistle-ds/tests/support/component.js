// Shared harness for the hidden tests. It boots the product's internal
// request-serving component in-process (the same module the product forks) and
// drives it over real loopback HTTP. Markers and scratch trees are created by
// the tests themselves; no product helper computes an expected value here.
'use strict';
var path = require('path');
var fs = require('fs');
var os = require('os');
var http = require('http');

var APP = process.env.WHISTLE_APP_ROOT || '/workspace';

function rand(prefix) {
  return prefix + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function makeRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'whistle-case-'));
}

// A fresh working tree per boot so cases never touch real user data.
function seed(env) {
  fs.mkdirSync(env.tempDir, { recursive: true });
  fs.mkdirSync(env.savedDir, { recursive: true });
  fs.mkdirSync(env.propsDir, { recursive: true });
  fs.mkdirSync(env.outsideDir, { recursive: true });

  env.secret = path.join(env.outsideDir, 'report.txt');
  env.secretContent = rand('OUT-OF-AREA-');
  fs.writeFileSync(env.secret, env.secretContent);

  env.hex = 'abcdef0123456789'.repeat(4); // 64 hex chars
  env.storedContent = rand('STORED-ITEM-');
  fs.writeFileSync(path.join(env.tempDir, env.hex), env.storedContent);

  env.savedName = rand('SAVED-INDEX-');
  var savedMonth = path.join(env.savedDir, '260101');
  fs.mkdirSync(savedMonth, { recursive: true });
  fs.writeFileSync(path.join(savedMonth, env.savedName + '_1_1700000000000'), '{}');
}

function boot(cb) {
  var root = makeRoot();
  var env = {
    root: root,
    tempDir: path.join(root, 'temp_files'),
    savedDir: path.join(root, 'saved_sessions'),
    propsDir: path.join(root, 'properties'),
    outsideDir: path.join(root, 'outside')
  };
  seed(env);
  var uid = 'cred-' + Math.random().toString(16).slice(2) + '-' + Date.now().toString(16);
  var startService = require(path.join(APP, 'lib/service/service.js'));
  startService({
    baseDir: root,
    storage: '',
    TEMP_FILES_PATH: env.tempDir,
    SAVED_SESSIONS_PATH: env.savedDir,
    propertiesDir: env.propsDir,
    uid: uid,
    clientId: 'client-' + Date.now().toString(16),
    clientIdNo: 0,
    port: 0
  }, function (err, info) {
    if (err) { return cb(err); }
    cb(null, { port: info.port, uid: uid, env: env });
  });
}

// The header name that carries the component's internal credential is defined
// once by the product (the panel already refers to it when it forwards
// requests). The tests read it from the product rather than hard-coding it.
function credHeaderName() {
  var common = require(path.join(APP, 'lib/util/common.js'));
  return common.WHISTLE_UID_HEADER;
}

function authHeaders(ctx, extra) {
  var h = {};
  var name = credHeaderName();
  h[name == null ? 'x-unset-credential' : name] = ctx.uid;
  if (extra) {
    Object.keys(extra).forEach(function (k) { h[k] = extra[k]; });
  }
  return h;
}

function wrongAuthHeaders(ctx) {
  var h = {};
  var name = credHeaderName();
  h[name == null ? 'x-unset-credential' : name] = 'not-' + ctx.uid;
  return h;
}

function request(ctx, method, urlPath, headers, body, cb) {
  var opts = {
    host: '127.0.0.1',
    port: ctx.port,
    path: urlPath,
    method: method,
    headers: headers || {}
  };
  var req = http.request(opts, function (res) {
    var chunks = [];
    res.on('data', function (d) { chunks.push(d); });
    res.on('end', function () {
      var buf = Buffer.concat(chunks);
      cb(null, { status: res.statusCode, body: buf.toString('utf8'), raw: buf });
    });
  });
  req.on('error', function (e) { cb(e); });
  if (body != null) { req.write(body); }
  req.end();
}

function get(ctx, urlPath, headers, cb) {
  request(ctx, 'GET', urlPath, headers, null, cb);
}

function postJson(ctx, urlPath, headers, value, cb) {
  var payload = JSON.stringify(value);
  var h = { 'content-type': 'application/json' };
  if (headers) { Object.keys(headers).forEach(function (k) { h[k] = headers[k]; }); }
  request(ctx, 'POST', urlPath, h, payload, cb);
}

function isClientError(status) {
  return status >= 400 && status < 500;
}

// True when the body carries the marker either literally or base64-encoded
// (one of the component's read paths returns items base64-encoded in a list).
function bodyLeaks(body, marker) {
  if (!body) { return false; }
  if (body.indexOf(marker) !== -1) { return true; }
  return body.indexOf(Buffer.from(marker).toString('base64')) !== -1;
}

module.exports = {
  APP: APP,
  boot: boot,
  get: get,
  request: request,
  postJson: postJson,
  authHeaders: authHeaders,
  wrongAuthHeaders: wrongAuthHeaders,
  credHeaderName: credHeaderName,
  isClientError: isClientError,
  bodyLeaks: bodyLeaks,
  rand: rand
};
