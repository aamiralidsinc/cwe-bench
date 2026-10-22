// Functional suite, part 1: a caller that presents the component's internal
// credential keeps full use of it. These cases encode the features an
// over-broad fix (one that confines all reads to the working area, refuses the
// authorised caller, or removes a route) would break. Every case PASSES on the
// vulnerable component and after a correct fix.
'use strict';
var H = require('../support/component.js');
var Suite = require('../support/junit.js').Suite;

var OUT = process.argv[2];
var suite = new Suite('functional-component');

function okJson(body) {
  try { return JSON.parse(body); } catch (e) { return null; }
}

H.boot(function (err, ctx) {
  if (err) {
    suite.test('boot internal component', function (done) { done(err); });
    return suite.run(OUT);
  }
  var env = ctx.env;

  suite.test('authorised load of a file by full path works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + encodeURIComponent(env.secret),
      H.authHeaders(ctx), function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.secretContent) === -1) {
          return done(new Error('authorised full-path load did not return the file (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('authorised read of a stored item works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + env.hex, H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      if (res.body.indexOf(env.storedContent) === -1) {
        return done(new Error('authorised stored read did not return the item (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  suite.test('authorised read via the list form works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?files=' + env.hex, H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      var j = okJson(res.body);
      var list = j && j.list;
      var got = Array.isArray(list) ? list.map(function (x) {
        try { return Buffer.from(x, 'base64').toString('utf8'); } catch (_) { return ''; }
      }).join('') : '';
      if (got.indexOf(env.storedContent) === -1) {
        return done(new Error('authorised list read did not return the item (status ' +
          res.status + ', body ' + res.body.slice(0, 80) + ')'));
      }
      done();
    });
  });

  suite.test('authorised create then read round-trips the content', function (done) {
    var content = H.rand('ROUNDTRIP-');
    H.postJson(ctx, '/cgi-bin/temp/create', H.authHeaders(ctx), { value: content },
      function (e, res) {
        if (e) { return done(e); }
        var j = okJson(res.body);
        if (!j || !j.filepath) {
          return done(new Error('authorised create did not return a handle (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        var handle = String(j.filepath).replace(/^\/?temp\//, '');
        H.get(ctx, '/cgi-bin/temp/get?filename=' + handle, H.authHeaders(ctx),
          function (e2, res2) {
            if (e2) { return done(e2); }
            if (res2.body.indexOf(content) === -1) {
              return done(new Error('round-trip read did not return the created content (status ' +
                res2.status + ')'));
            }
            done();
          });
      });
  });

  suite.test('authorised access to the stored-session index works', function (done) {
    H.get(ctx, '/cgi-bin/saved/list', H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      var j = okJson(res.body);
      if (!j || j.ec !== 0) {
        return done(new Error('authorised index access failed (status ' + res.status +
          ', body ' + res.body.slice(0, 80) + ')'));
      }
      if (res.body.indexOf(env.savedName) === -1) {
        return done(new Error('authorised index did not include the saved session'));
      }
      done();
    });
  });

  suite.test('authorised access to request history works', function (done) {
    H.get(ctx, '/cgi-bin/history', H.authHeaders(ctx), function (e, res) {
      if (e) { return done(e); }
      if (res.status !== 200 || !Array.isArray(okJson(res.body))) {
        return done(new Error('authorised history access failed (status ' + res.status +
          ', body ' + res.body.slice(0, 80) + ')'));
      }
      done();
    });
  });

  suite.test('authorised load through the recovery path works', function (done) {
    H.get(ctx, '/cgi-bin/composer/recover?file=' + encodeURIComponent(env.secret),
      H.authHeaders(ctx), function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.secretContent) === -1) {
          return done(new Error('authorised recovery load did not return the file (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.run(OUT);
});
