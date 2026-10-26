// Local HTTP service for the request-following cases. The verifier starts it as root before the
// suites run and reserves its names in the container hosts file; nothing leaves the container.
const http = require('http');
const fs = require('fs');

const requested = Number(process.env.TEST_PORT || '0');

function redirect(res, location) {
  res.writeHead(302, { Location: location });
  res.end();
}

const server = http.createServer((req, res) => {
  const port = server.address().port;
  const path = req.url || '/';
  if (path.startsWith('/hopcred-user')) {
    return redirect(res, `http://user@internal.invalid:${port}/final`);
  }
  if (path.startsWith('/hopcred-pass')) {
    return redirect(res, `http://user:pass@internal.invalid:${port}/final`);
  }
  if (path.startsWith('/hopcred-passonly')) {
    return redirect(res, `http://:pass@internal.invalid:${port}/final`);
  }
  if (path.startsWith('/redir')) {
    return redirect(res, `http://plain.invalid:${port}/final`);
  }
  res.writeHead(200, { 'content-type': 'text/plain' });
  res.end('ok');
});

server.listen(requested, '127.0.0.1', () => {
  if (process.env.PORT_FILE) {
    fs.writeFileSync(process.env.PORT_FILE, String(server.address().port));
  }
});
