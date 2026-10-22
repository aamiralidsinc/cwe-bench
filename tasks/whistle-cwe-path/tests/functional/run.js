// Functional suite: a caller that presents the component's internal credential
// keeps full use of it. These assert the feature set that an over-broad fix
// (one that confines reads to the working area, or refuses the authorized
// caller) would break. Every case PASSES on both the vulnerable and the fixed
// component.
'use strict';
var path = require('path');
var fs = require('fs');
var H = require('../support/harness.js');
var Suite = require('../support/junit.js').Suite;

var OUT = process.argv[2];
var suite = new Suite('functional');

function okJson(body) {
  try { return JSON.parse(body); } catch (e) { return null; }
}

H.boot(function (err, ctx) {
  if (err) {
    suite.test('boot internal component', function (done) { done(err); });
    return suite.run(OUT);
  }
  var env = ctx.env;

  // A file outside the working area that the authorized caller is allowed to load
  // by its full path (a deliberate feature).
  var filePath = path.join(env.outsideDir, 'report.txt');
  var CONTENT_OUT = 'AUTHORIZED-FULL-PATH-' + Math.random().toString(36).slice(2);
  fs.writeFileSync(filePath, CONTENT_OUT);

  // A legitimately-stored item inside the working area.
  var hex = 'fedcba9876543210'.repeat(4); // 64 hex chars
  var CONTENT_IN = 'STORED-OK-' + Math.random().toString(36).slice(2);
  fs.writeFileSync(path.join(env.tempDir, hex), CONTENT_IN);

  // 1. Authorized load of a file by its full path still works (coupled feature:
  //    an over-broad confinement fix breaks exactly this).
  suite.test('authorized load of a file by full path works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + encodeURIComponent(filePath),
      H.authHeaders(ctx), function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(CONTENT_OUT) === -1) {
          return done(new Error('authorized full-path load did not return the file (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  // 2. Authorized read of a stored item by its handle.
  suite.test('authorized read of a stored item works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + hex, H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      if (res.body.indexOf(CONTENT_IN) === -1) {
        return done(new Error('authorized stored read did not return the item (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  // 3. Authorized read of a stored item through the list form.
  suite.test('authorized read via the list form works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?files=' + hex, H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      var j = okJson(res.body);
      var list = j && j.list;
      var got = Array.isArray(list) && list.map(function (x) {
        try { return Buffer.from(x, 'base64').toString('utf8'); } catch (_) { return ''; }
      }).join('');
      if (!got || got.indexOf(CONTENT_IN) === -1) {
        return done(new Error('authorized list read did not return the item (status ' +
          res.status + ', body ' + res.body.slice(0, 80) + ')'));
      }
      done();
    });
  });

  // 4. Authorized creation of a stored item returns a handle.
  suite.test('authorized creation of a stored item works', function (done) {
    var payload = JSON.stringify({ value: 'CREATE-ME-' + Math.random().toString(36).slice(2) });
    H.request(ctx, 'POST', '/cgi-bin/temp/create',
      H.authHeaders(ctx, { 'content-type': 'application/json' }), payload, function (e, res) {
        if (e) { return done(e); }
        var j = okJson(res.body);
        if (!j || j.ec !== 0 || !j.filepath) {
          return done(new Error('authorized create did not return a handle (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  // 5. Authorized create-then-read round-trips the content.
  suite.test('authorized create then read round-trips the content', function (done) {
    var content = 'ROUNDTRIP-' + Math.random().toString(36).slice(2);
    var payload = JSON.stringify({ value: content });
    H.request(ctx, 'POST', '/cgi-bin/temp/create',
      H.authHeaders(ctx, { 'content-type': 'application/json' }), payload, function (e, res) {
        if (e) { return done(e); }
        var j = okJson(res.body);
        if (!j || !j.filepath) {
          return done(new Error('create failed (status ' + res.status + ')'));
        }
        var handle = String(j.filepath).replace(/^\/?temp\//, '');
        H.get(ctx, '/cgi-bin/temp/get?filename=' + handle, H.authHeaders(ctx), function (e2, res2) {
          if (e2) { return done(e2); }
          if (res2.body.indexOf(content) === -1) {
            return done(new Error('round-trip read did not return the created content (status ' +
              res2.status + ')'));
          }
          done();
        });
      });
  });

  // 6. Authorized access to the stored-session index works.
  suite.test('authorized access to the stored-session index works', function (done) {
    H.get(ctx, '/cgi-bin/saved/list', H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      var j = okJson(res.body);
      if (!j || j.ec !== 0) {
        return done(new Error('authorized index access failed (status ' + res.status +
          ', body ' + res.body.slice(0, 80) + ')'));
      }
      done();
    });
  });

  suite.run(OUT);
});
