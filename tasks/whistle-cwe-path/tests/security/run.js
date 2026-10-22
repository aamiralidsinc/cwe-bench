// Security suite: an attacker who does not present the component's internal
// credential (or presents a wrong one) must not be able to make it read any
// file, write anything, or return any internal
// data. Every case drives the component over real HTTP without a valid credential and
// asserts the attempt is refused with a client error and no data leaks.
//
// All cases FAIL on the vulnerable code (the component answers anyone) and PASS
// once the component only serves requests carrying its credential.
'use strict';
var path = require('path');
var fs = require('fs');
var H = require('../support/harness.js');
var Suite = require('../support/junit.js').Suite;

var OUT = process.argv[2];
var suite = new Suite('security');

function isClientError(status) {
  return status >= 400 && status < 500;
}

H.boot(function (err, ctx) {
  if (err) {
    // Boot failure is an environment problem; surface it as a single failure.
    suite.test('boot internal component', function (done) { done(err); });
    return suite.run(OUT);
  }
  var env = ctx.env;

  // A marker file placed OUTSIDE the component's working area.
  var secretPath = path.join(env.outsideDir, 'secret.txt');
  var MARKER_OUT = 'OUT-OF-AREA-MARKER-' + Math.random().toString(36).slice(2);
  fs.writeFileSync(secretPath, MARKER_OUT);

  // A legitimately-stored item inside the working area, named by a 64-hex handle.
  var hex = 'abcdef0123456789'.repeat(4); // 64 hex chars
  var MARKER_IN = 'STORED-ITEM-MARKER-' + Math.random().toString(36).slice(2);
  fs.writeFileSync(path.join(env.tempDir, hex), MARKER_IN);

  // 1. Read a file outside the working area (the headline arbitrary read).
  suite.test('unauthenticated read of a file outside the working area is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + encodeURIComponent(secretPath), {}, function (e, res) {
      if (e) { return done(e); }
      if (res.body.indexOf(MARKER_OUT) !== -1) {
        return done(new Error('file content leaked to an unauthenticated caller'));
      }
      if (!isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  // 2. Read a legitimately-stored item by its handle: still off-limits without
  //    the credential (the guard is about who is asking, not only where it points).
  suite.test('unauthenticated read of a stored item is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + hex, {}, function (e, res) {
      if (e) { return done(e); }
      if (res.body.indexOf(MARKER_IN) !== -1) {
        return done(new Error('stored item leaked to an unauthenticated caller'));
      }
      if (!isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  // 3. Same stored item, requested through the batch/list form of the same read.
  suite.test('unauthenticated read via the list form is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?files=' + hex, {}, function (e, res) {
      if (e) { return done(e); }
      // The list form base64-encodes each item; decode anything that looks encoded.
      var leaked = res.body.indexOf(MARKER_IN) !== -1 ||
        res.body.indexOf(Buffer.from(MARKER_IN).toString('base64')) !== -1;
      if (leaked) {
        return done(new Error('stored item leaked via the list form'));
      }
      if (!isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  // 4. A non-file internal data route: the index of stored sessions.
  suite.test('unauthenticated access to the stored-session index is refused', function (done) {
    H.get(ctx, '/cgi-bin/saved/list', {}, function (e, res) {
      if (e) { return done(e); }
      if (!isClientError(res.status)) {
        return done(new Error('internal data route answered an unauthenticated caller (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  // 5. Another non-file internal data route: request history.
  suite.test('unauthenticated access to request history is refused', function (done) {
    H.get(ctx, '/cgi-bin/history', {}, function (e, res) {
      if (e) { return done(e); }
      if (!isClientError(res.status)) {
        return done(new Error('internal data route answered an unauthenticated caller (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  // 6. A credential that is present but wrong must be refused just like a
  //    missing one (the guard checks the value, not merely that something was sent).
  suite.test('read with a wrong-valued credential is refused', function (done) {
    var headers = {};
    var name = H.credHeaderName();
    if (name != null) {
      headers[name] = 'not-' + ctx.uid;
    }
    H.get(ctx, '/cgi-bin/temp/get?filename=' + encodeURIComponent(secretPath), headers, function (e, res) {
      if (e) { return done(e); }
      if (res.body.indexOf(MARKER_OUT) !== -1) {
        return done(new Error('file content leaked to a caller with a wrong credential'));
      }
      if (!isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  // 7. A non-read operation: an unauthenticated create must be refused and must
  //    not write anything into the working area.
  suite.test('unauthenticated creation of a stored item is refused', function (done) {
    var before = fs.readdirSync(env.tempDir).sort().join('\n');
    var payload = JSON.stringify({ value: 'ANON-CREATE-' + Math.random().toString(36).slice(2) });
    H.request(ctx, 'POST', '/cgi-bin/temp/create', { 'content-type': 'application/json' }, payload,
      function (e, res) {
        if (e) { return done(e); }
        setTimeout(function () {
          var after = fs.readdirSync(env.tempDir).sort().join('\n');
          if (after !== before) {
            return done(new Error('unauthenticated create wrote to the working area'));
          }
          if (!isClientError(res.status)) {
            return done(new Error('expected a client error, got status ' + res.status));
          }
          done();
        }, 200);
      });
  });

  suite.run(OUT);
});
