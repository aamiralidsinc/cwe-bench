// Security suite, part 2: when panel login is configured, an unauthenticated
// caller must not be able to make the panel read a host file. These cases drive
// the real panel application over loopback HTTP with no credentials and assert a
// client error with no content returned.
//
// All cases FAIL on the vulnerable panel (it reads the file and returns it) and
// PASS once the panel establishes who is calling before performing the action.
'use strict';
var path = require('path');
var H = require('../support/panel.js');
var Suite = require('../support/junit.js').Suite;

var OUT = process.argv[2];
var suite = new Suite('security-panel');

H.boot(function (err, ctx) {
  if (err) {
    suite.test('boot control panel', function (done) { done(err); });
    return suite.run(OUT);
  }
  var env = ctx.env;
  suite.onDone(function () { ctx.close(); });

  function refused(label, urlPath, marker, headers, done) {
    H.get(ctx, urlPath, { headers: headers }, function (e, res) {
      if (e) { return done(e); }
      if (H.bodyLeaks(res.body, marker)) {
        return done(new Error(label + ': file content returned to an unauthenticated caller'));
      }
      if (!H.isClientError(res.status)) {
        return done(new Error(label + ': expected a client error, got status ' + res.status));
      }
      done();
    });
  }

  suite.test('unauthenticated panel import of a path outside the working area is refused', function (done) {
    refused('import', '/cgi-bin/import-remote?url=' + encodeURIComponent(env.secret),
      env.secretContent, null, done);
  });

  suite.test('unauthenticated panel import of a stored item is refused', function (done) {
    refused('import', '/cgi-bin/import-remote?url=' + encodeURIComponent(env.hex),
      env.storedContent, null, done);
  });

  suite.test('unauthenticated panel download of a path outside the working area is refused', function (done) {
    refused('download', '/cgi-bin/temp/download?filename=' + encodeURIComponent(env.secret),
      env.secretContent, null, done);
  });

  suite.test('unauthenticated panel download of a stored item is refused', function (done) {
    refused('download', '/cgi-bin/temp/download?filename=' + encodeURIComponent(env.hex),
      env.storedContent, null, done);
  });

  suite.test('unauthenticated panel body load from a path outside the working area is refused', function (done) {
    refused('body load', '/cgi-bin/composer/local-body?file=' + encodeURIComponent(env.secret),
      env.secretContent, { host: 'localhost' }, done);
  });

  suite.test('unauthenticated panel body load of a stored item is refused', function (done) {
    refused('body load', '/cgi-bin/composer/local-body?file=' + encodeURIComponent(env.hex),
      env.storedContent, { host: 'localhost' }, done);
  });

  suite.test('unauthenticated panel draft load of a path outside the working area is refused', function (done) {
    refused('draft', '/cgi-bin/composer/draft?file=' + encodeURIComponent(env.secret),
      env.secretContent, null, done);
  });

  suite.test('unauthenticated panel draft load of a stored item is refused', function (done) {
    refused('draft', '/cgi-bin/composer/draft?file=' +
      encodeURIComponent(path.join(env.tempDir, env.hex)), env.storedContent, null, done);
  });

  suite.run(OUT);
});
