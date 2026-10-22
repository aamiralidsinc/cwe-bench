// Security suite, part 1: the background data component must act only on
// requests that carry its own internal credential. Every case drives it over
// real loopback HTTP with no credential (or a wrong one) and asserts that the
// attempt is refused with a client error and leaks nothing.
//
// All cases FAIL on the vulnerable component (it answers anyone) and PASS once
// it only serves requests carrying its credential.
'use strict';
var fs = require('fs');
var path = require('path');
var H = require('../support/component.js');
var Suite = require('../support/junit.js').Suite;

var OUT = process.argv[2];
var suite = new Suite('security-component');

H.boot(function (err, ctx) {
  if (err) {
    suite.test('boot internal component', function (done) { done(err); });
    return suite.run(OUT);
  }
  var env = ctx.env;

  suite.test('unauthenticated read of a file outside the working area is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + encodeURIComponent(env.secret), {}, function (e, res) {
      if (e) { return done(e); }
      if (H.bodyLeaks(res.body, env.secretContent)) {
        return done(new Error('file content leaked to an unauthenticated caller'));
      }
      if (!H.isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  suite.test('unauthenticated read of a stored item is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + env.hex, {}, function (e, res) {
      if (e) { return done(e); }
      if (H.bodyLeaks(res.body, env.storedContent)) {
        return done(new Error('stored item leaked to an unauthenticated caller'));
      }
      if (!H.isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  suite.test('unauthenticated read via the list form is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?files=' + env.hex, {}, function (e, res) {
      if (e) { return done(e); }
      if (H.bodyLeaks(res.body, env.storedContent)) {
        return done(new Error('stored item leaked via the list form'));
      }
      if (!H.isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  suite.test('unauthenticated creation of a stored item is refused', function (done) {
    var before = fs.readdirSync(env.tempDir).sort().join('\n');
    H.postJson(ctx, '/cgi-bin/temp/create', {}, { value: H.rand('ANON-CREATE-') }, function (e, res) {
      if (e) { return done(e); }
      setTimeout(function () {
        var after = fs.readdirSync(env.tempDir).sort().join('\n');
        if (after !== before) {
          return done(new Error('unauthenticated create wrote to the working area'));
        }
        if (!H.isClientError(res.status)) {
          return done(new Error('expected a client error, got status ' + res.status));
        }
        done();
      }, 200);
    });
  });

  suite.test('unauthenticated listing of saved sessions is refused', function (done) {
    H.get(ctx, '/cgi-bin/saved/list', {}, function (e, res) {
      if (e) { return done(e); }
      if (H.bodyLeaks(res.body, env.savedName)) {
        return done(new Error('saved-session index leaked to an unauthenticated caller'));
      }
      if (!H.isClientError(res.status)) {
        return done(new Error('internal data route answered an unauthenticated caller (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  suite.test('unauthenticated read of a saved session is refused', function (done) {
    var time = 1700000000000;
    var name = H.rand('ANON-SAVED-');
    var date = new Date(time);
    var month = String(date.getFullYear()) + ('0' + (date.getMonth() + 1)).slice(-2);
    var dir = path.join(env.savedDir, month);
    var content = H.rand('SAVED-SESSION-CONTENT-');
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, name + '_0_' + time), content);
    H.get(ctx, '/cgi-bin/saved/sessions?filename=' + encodeURIComponent(name) +
      '&time=' + time + '&count=0', {}, function (e, res) {
      if (e) { return done(e); }
      if (H.bodyLeaks(res.body, content)) {
        return done(new Error('saved-session content leaked to an unauthenticated caller'));
      }
      if (!H.isClientError(res.status)) {
        return done(new Error('expected a client error, got status ' + res.status));
      }
      done();
    });
  });

  suite.test('unauthenticated access to request history is refused', function (done) {
    H.get(ctx, '/cgi-bin/history', {}, function (e, res) {
      if (e) { return done(e); }
      if (!H.isClientError(res.status)) {
        return done(new Error('internal data route answered an unauthenticated caller (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  suite.test('a credential that is present but wrong is refused', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + encodeURIComponent(env.secret),
      H.wrongAuthHeaders(ctx), function (e, res) {
        if (e) { return done(e); }
        if (H.bodyLeaks(res.body, env.secretContent)) {
          return done(new Error('file content leaked to a caller with a wrong credential'));
        }
        if (!H.isClientError(res.status)) {
          return done(new Error('expected a client error, got status ' + res.status));
        }
        done();
      });
  });

  suite.test('unauthenticated load through the recovery path is refused', function (done) {
    H.get(ctx, '/cgi-bin/composer/recover?file=' + encodeURIComponent(env.secret), {},
      function (e, res) {
        if (e) { return done(e); }
        if (H.bodyLeaks(res.body, env.secretContent)) {
          return done(new Error('file content leaked to an unauthenticated caller'));
        }
        if (!H.isClientError(res.status)) {
          return done(new Error('expected a client error, got status ' + res.status));
        }
        done();
      });
  });

  suite.test('a credential that is present but wrong is refused on the recovery path', function (done) {
    H.get(ctx, '/cgi-bin/composer/recover?file=' + encodeURIComponent(env.secret),
      H.wrongAuthHeaders(ctx), function (e, res) {
        if (e) { return done(e); }
        if (H.bodyLeaks(res.body, env.secretContent)) {
          return done(new Error('file content leaked to a caller with a wrong credential'));
        }
        if (!H.isClientError(res.status)) {
          return done(new Error('expected a client error, got status ' + res.status));
        }
        done();
      });
  });

  suite.run(OUT);
});
