'use strict';

const http = require('node:http');

/// Serve the given path -> Buffer map on loopback. Everything else is a 404.
async function startServer(routes) {
  const server = http.createServer((req, res) => {
    const pathname = new URL(req.url, 'http://localhost').pathname;
    if (Object.prototype.hasOwnProperty.call(routes, pathname)) {
      res.writeHead(200, { 'content-type': 'application/octet-stream' });
      res.end(routes[pathname]);
    } else {
      res.writeHead(404);
      res.end();
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  return {
    url: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}

/// Construct a fresh client pointed at `url` for the duration of `fn`.
async function withRemote(routes, fn) {
  const server = await startServer(routes);
  process.env.NX_SELF_HOSTED_REMOTE_CACHE_SERVER = server.url;
  try {
    const { native } = require('./nx');
    const HttpRemoteCache = native().HttpRemoteCache;
    return await fn(new HttpRemoteCache(), server);
  } finally {
    await server.close();
  }
}

module.exports = { startServer, withRemote };
