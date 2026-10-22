// Shared harness for the hidden tests. It boots the product's internal
// request-serving component (an in-process HTTP server on 127.0.0.1, exactly
// as the product boots it) and drives it over real HTTP. Nothing here encodes
// the expected fix; the tests compute their own markers and clean up their own
// scratch files.
'use strict';
var path = require('path');
var fs = require('fs');
var os = require('os');
var http = require('http');

var APP = process.env.WHISTLE_APP_ROOT || '/app';

// A fresh working tree per run so cases never collide with real data.
function freshRoot() {
  var root = fs.mkdtempSync(path.join(os.tmpdir(), 'whistle-case-'));
  var env = {
    root: root,
    tempDir: path.join(root, 'temp_files'),
    savedDir: path.join(root, 'saved_sessions'),
    propsDir: path.join(root, 'properties'),
    outsideDir: path.join(root, 'outside')
  };
  fs.mkdirSync(env.tempDir, { recursive: true });
  fs.mkdirSync(env.savedDir, { recursive: true });
  fs.mkdirSync(env.propsDir, { recursive: true });
  fs.mkdirSync(env.outsideDir, { recursive: true });
  process.env.WHISTLE_PATH = root;
  return env;
}

// Boot the internal service component the way the product does.
function boot(cb) {
  var env = freshRoot();
  // A distinct per-run credential value; the product reads it from its config.
  var uid = 'cred-' + Math.random().toString(16).slice(2) + '-' + Date.now().toString(16);
  var startService = require(path.join(APP, 'lib/service/service.js'));
  var options = {
    baseDir: env.root,
    storage: '',
    TEMP_FILES_PATH: env.tempDir,
    SAVED_SESSIONS_PATH: env.savedDir,
    propertiesDir: env.propsDir,
    uid: uid,
    clientId: 'client-' + Date.now().toString(16),
    clientIdNo: 0,
    port: 0
  };
  startService(options, function (err, info) {
    if (err) {
      return cb(err);
    }
    cb(null, { port: info.port, uid: uid, env: env });
  });
}

// The header name the product uses to carry its internal credential is fixed
// by code that already calls the component (the UI layer). A correct
// implementation must honour whatever name the product defines, so the tests
// read it from the product rather than hard-coding a spelling.
function credHeaderName() {
  var common = require(path.join(APP, 'lib/util/common.js'));
  return common.WHISTLE_UID_HEADER;
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
      cb(null, { status: res.statusCode, body: Buffer.concat(chunks).toString('utf8') });
    });
  });
  req.on('error', function (e) { cb(e); });
  if (body != null) {
    req.write(body);
  }
  req.end();
}

function get(ctx, urlPath, headers, cb) {
  request(ctx, 'GET', urlPath, headers, null, cb);
}

// A request carrying the product's valid internal credential.
function authHeaders(ctx, extra) {
  var h = {};
  var name = credHeaderName();
  if (name != null) {
    h[name] = ctx.uid;
  }
  if (extra) {
    Object.keys(extra).forEach(function (k) { h[k] = extra[k]; });
  }
  return h;
}

module.exports = {
  boot: boot,
  get: get,
  request: request,
  authHeaders: authHeaders,
  credHeaderName: credHeaderName
};
