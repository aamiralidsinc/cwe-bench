// Harness for the control panel's own HTTP interface. It mounts the real panel
// application on a loopback listener the way the product does when the panel is
// served on its own port, with a real background data component forked by the
// panel's normal forwarding path. Login is configured so that unauthenticated
// callers are observable.
'use strict';
var path = require('path');
var fs = require('fs');
var os = require('os');
var http = require('http');
var EventEmitter = require('events');

var APP = process.env.WHISTLE_APP_ROOT || '/workspace';

var USER = 'admin';
var PASS = 'pw-' + Math.random().toString(36).slice(2);

function rand(prefix) {
  return prefix + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function killServiceChildren(root) {
  var dirs;
  try { dirs = fs.readdirSync('/proc'); } catch (e) { return; }
  dirs.forEach(function (pid) {
    if (!/^\d+$/.test(pid)) { return; }
    var cmd;
    try {
      cmd = fs.readFileSync('/proc/' + pid + '/cmdline', 'utf8').replace(/\0/g, ' ');
    } catch (e) { return; }
    if (cmd.indexOf(path.join(root, 'lib', 'service', 'service.js')) !== -1 ||
        cmd.indexOf(APP + '/lib/service/service.js') !== -1) {
      try { process.kill(+pid, 'SIGKILL'); } catch (e) {}
    }
  });
}

function boot(cb) {
  var root = fs.mkdtempSync(path.join(os.tmpdir(), 'whistle-panel-'));
  // Paths are resolved when the product's configuration module first loads.
  process.env.WHISTLE_PATH = root;
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

  env.secret = path.join(env.outsideDir, 'report.txt');
  env.secretContent = rand('PANEL-OUT-OF-AREA-');
  fs.writeFileSync(env.secret, env.secretContent);

  env.hex = 'fedcba9876543210'.repeat(4);
  env.storedContent = rand('PANEL-STORED-');
  fs.writeFileSync(path.join(env.tempDir, env.hex), env.storedContent);

  var config = require(path.join(APP, 'lib/config'));
  config.baseDir = root;
  config.TEMP_FILES_PATH = env.tempDir;
  config.SAVED_SESSIONS_PATH = env.savedDir;
  config.propertiesDir = env.propsDir;
  config.storage = '';
  config.extend({});
  // Access control is configured for this panel.
  config.username = USER;
  config.password = PASS;

  var ui = require(path.join(APP, 'biz/webui/lib'));
  var util = require(path.join(APP, 'lib/util'));
  var pluginMgr = require(path.join(APP, 'lib/plugins'));
  var proxy = new EventEmitter();
  proxy.pluginMgr = pluginMgr;
  proxy.util = util;
  proxy.config = config;
  ui.init(proxy);

  var server = http.createServer();
  ui.setupServer(server);
  server.on('error', cb);
  server.listen(0, '127.0.0.1', function () {
    cb(null, {
      port: server.address().port,
      env: env,
      user: USER,
      pass: PASS,
      close: function () {
        try { server.close(); } catch (e) {}
        killServiceChildren(APP);
        killServiceChildren(root);
      }
    });
  });
}

function authorization(ctx) {
  return 'Basic ' + Buffer.from(ctx.user + ':' + ctx.pass).toString('base64');
}

function request(ctx, method, urlPath, opts, body, cb) {
  opts = opts || {};
  var headers = {};
  if (opts.auth) { headers.authorization = authorization(ctx); }
  if (opts.headers) {
    Object.keys(opts.headers).forEach(function (k) { headers[k] = opts.headers[k]; });
  }
  var req = http.request({
    host: '127.0.0.1',
    port: ctx.port,
    path: urlPath,
    method: method,
    headers: headers
  }, function (res) {
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

function get(ctx, urlPath, opts, cb) {
  request(ctx, 'GET', urlPath, opts, null, cb);
}

function postJson(ctx, urlPath, opts, value, cb) {
  opts = opts || {};
  var headers = {};
  if (opts.headers) {
    Object.keys(opts.headers).forEach(function (k) { headers[k] = opts.headers[k]; });
  }
  headers['content-type'] = 'application/json';
  request(ctx, 'POST', urlPath, { auth: opts.auth, headers: headers },
    JSON.stringify(value), cb);
}

function isClientError(status) {
  return status >= 400 && status < 500;
}

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
  isClientError: isClientError,
  bodyLeaks: bodyLeaks,
  rand: rand
};
