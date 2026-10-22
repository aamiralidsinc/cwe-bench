// Functional suite, part 2: an authenticated operator keeps full use of the
// panel. These cases encode the features an over-broad fix (one that removes a
// route, refuses every local path, or blocks the panel's forwarding) would
// break. Every case PASSES on the vulnerable panel and after a correct fix.
'use strict';
var path = require('path');
var H = require('../support/panel.js');
var Suite = require('../support/junit.js').Suite;

var OUT = process.argv[2];
var suite = new Suite('functional-panel');

function okJson(body) {
  try { return JSON.parse(body); } catch (e) { return null; }
}

H.boot(function (err, ctx) {
  if (err) {
    suite.test('boot control panel', function (done) { done(err); });
    return suite.run(OUT);
  }
  var env = ctx.env;
  suite.onDone(function () { ctx.close(); });

  suite.test('authenticated import of a file by full path works', function (done) {
    H.get(ctx, '/cgi-bin/import-remote?url=' + encodeURIComponent(env.secret),
      { auth: true }, function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.secretContent) === -1) {
          return done(new Error('authenticated import did not return the file (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('authenticated panel read of a stored item works', function (done) {
    H.get(ctx, '/cgi-bin/temp/get?filename=' + env.hex, { auth: true }, function (e, res) {
      if (e) { return done(e); }
      if (res.body.indexOf(env.storedContent) === -1) {
        return done(new Error('authenticated stored read failed (status ' + res.status +
          ', body ' + res.body.slice(0, 80) + ')'));
      }
      done();
    });
  });

  suite.test('authenticated panel creation of a stored item works', function (done) {
    H.postJson(ctx, '/cgi-bin/temp/create', { auth: true },
      { value: H.rand('PANEL-CREATE-') }, function (e, res) {
        if (e) { return done(e); }
        var j = okJson(res.body);
        if (!j || j.ec !== 0 || !j.filepath) {
          return done(new Error('authenticated create failed (status ' + res.status +
            ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('authenticated panel download of a file by full path works', function (done) {
    H.get(ctx, '/cgi-bin/temp/download?filename=' + encodeURIComponent(env.secret),
      { auth: true }, function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.secretContent) === -1) {
          return done(new Error('authenticated download failed (status ' + res.status +
            ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('authenticated panel body load from a file by full path works', function (done) {
    H.get(ctx, '/cgi-bin/composer/local-body?file=' + encodeURIComponent(env.secret),
      { auth: true, headers: { host: 'localhost' } }, function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.secretContent) === -1) {
          return done(new Error('authenticated body load failed (status ' + res.status +
            ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('authenticated panel draft load from a file by full path works', function (done) {
    H.get(ctx, '/cgi-bin/composer/draft?file=' + encodeURIComponent(env.secret),
      { auth: true }, function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.secretContent) === -1) {
          return done(new Error('authenticated draft load failed (status ' + res.status +
            ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('authenticated panel draft load of a stored item works', function (done) {
    H.get(ctx, '/cgi-bin/composer/draft?file=' +
      encodeURIComponent(path.join(env.tempDir, env.hex)),
      { auth: true }, function (e, res) {
        if (e) { return done(e); }
        if (res.body.indexOf(env.storedContent) === -1) {
          return done(new Error('authenticated stored-item draft load failed (status ' +
            res.status + ', body ' + res.body.slice(0, 80) + ')'));
        }
        done();
      });
  });

  suite.test('unauthenticated load of panel metadata still works', function (done) {
    H.get(ctx, '/cgi-bin/plugins/get-plugins', {}, function (e, res) {
      if (e) { return done(e); }
      var j = okJson(res.body);
      if (res.status !== 200 || !j || j.ec !== 0) {
        return done(new Error('the panel metadata route did not answer without login (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  // Static assets are deliberately exempt from the panel's login check; an
  // over-broad auth rule breaks the panel's asset loading.
  suite.test('unauthenticated load of panel assets still works', function (done) {
    H.get(ctx, '/js/index.js', {}, function (e, res) {
      if (e) { return done(e); }
      if (res.status !== 200 || !res.body.length) {
        return done(new Error('the panel asset did not load without login (status ' +
          res.status + ')'));
      }
      done();
    });
  });

  suite.run(OUT);
});
