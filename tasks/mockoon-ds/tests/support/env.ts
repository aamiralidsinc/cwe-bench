/**
 * Shared harness for the hidden verifier suites.
 *
 * Everything here drives the product through its real entry points: the public
 * server class starts a real HTTP/WebSocket listener, and the serverless
 * wrapper's request listener is mounted on a real HTTP server. Expected values
 * are computed in the tests themselves; nothing here calls product helpers to
 * decide what is correct.
 */
import assert from 'node:assert';
import { createServer } from 'node:http';
import { Writable } from 'node:stream';
import { createLogger, format as logFormat, transports } from 'winston';
import WebSocket from 'ws';

export const DEFAULT_PREFIX = 'MOCKOON_';
export const TXN_MARKER = 'TXN-MARKER-VALUE';
export const TXN_URL = '/hello';
export const SECRET_AUTH = 'SECRET-AUTH-VALUE-9137';
export const SECRET_COOKIE = 'SECRET-COOKIE-VALUE-9137';
export const SECRET_APIKEY = 'SECRET-APIKEY-VALUE-9137';
export const SECRET_XAUTH = 'SECRET-XAUTH-VALUE-9137';

export const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export const allocator = (base: number) => {
  let next = base;
  return () => next++;
};

export const makeEnvironment = (port: number, overrides: any = {}) => ({
  uuid: '11111111-1111-4111-8111-111111111111',
  lastMigration: 33,
  name: 'verifier-env',
  port,
  hostname: '127.0.0.1',
  endpointPrefix: '',
  latency: 0,
  routes: [
    {
      uuid: '22222222-2222-4222-8222-222222222222',
      type: 'http',
      documentation: '',
      method: 'get',
      endpoint: 'hello',
      responses: [
        {
          uuid: '33333333-3333-4333-8333-333333333333',
          body: 'hello-body',
          latency: 0,
          statusCode: 200,
          label: '',
          headers: [],
          bodyType: 'INLINE',
          filePath: '',
          databucketID: '',
          sendFileAsBody: false,
          rules: [],
          rulesOperator: 'OR',
          disableTemplating: false,
          fallbackTo404: false,
          default: true,
          crudKey: 'id',
          callbacks: []
        }
      ],
      responseMode: null,
      streamingMode: null,
      streamingInterval: 0
    }
  ],
  proxyMode: false,
  proxyRemovePrefix: false,
  proxyHost: '',
  proxyReqHeaders: [],
  proxyResHeaders: [],
  cors: false,
  headers: [{ key: 'Content-Type', value: 'text/plain' }],
  tlsOptions: {
    enabled: false,
    type: 'CERT',
    pfxPath: '',
    certPath: '',
    keyPath: '',
    caPath: '',
    passphrase: ''
  },
  data: [],
  folders: [],
  rootChildren: [{ type: 'route', uuid: '22222222-2222-4222-8222-222222222222' }],
  callbacks: [],
  ...overrides
});

export const authHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`
});

export const request = async (url: string, init: any = {}, ms = 4000) => {
  const res = await fetch(url, { ...init, signal: AbortSignal.timeout(ms) });
  const text = await res.text();
  return { status: res.status, headers: res.headers, text };
};

export const startServer = async (
  client: any,
  options: any = {},
  envOverrides: any = {},
  port = 4300
) => {
  const environment = makeEnvironment(port, envOverrides);
  const server = new client(environment, options);
  await new Promise<void>((resolve, reject) => {
    server.on('started', () => resolve());
    server.on('error', (error: any) =>
      reject(new Error(`server error: ${JSON.stringify(error)}`))
    );
    server.start();
  });
  return { server, port, base: `http://127.0.0.1:${port}` };
};

export const stopServer = async (server: any) => {
  try {
    server.stop();
  } catch {
    /* already stopped */
  }
  await delay(120);
};

/**
 * Start a real server, run `fn`, always stop it.
 */
export const withServer = async (
  client: any,
  options: any,
  fn: (ctx: { server: any; port: number; base: string }) => Promise<void>,
  envOverrides: any = {},
  port = 4300
) => {
  const ctx = await startServer(client, options, envOverrides, port);
  try {
    await fn(ctx);
  } finally {
    await stopServer(ctx.server);
  }
};

/**
 * Send one request to the mock route carrying credentials and a marker header,
 * then wait for the transaction to be recorded.
 */
export const seedTransaction = async (
  base: string,
  extraHeaders: any = {},
  marker = TXN_MARKER
) => {
  await request(`${base}${TXN_URL}`, {
    headers: {
      Authorization: `Bearer ${SECRET_AUTH}`,
      Cookie: `session=${SECRET_COOKIE}`,
      'x-api-key': SECRET_APIKEY,
      'x-auth-token': SECRET_XAUTH,
      'x-txn-marker': marker,
      ...extraHeaders
    }
  });
  await delay(100);
};

/**
 * Read an HTTP response body for up to `ms`, tolerating a stream that never
 * ends (event streams, rejected upgrades that keep the socket open).
 */
export const readFor = async (url: string, init: any = {}, ms = 600) => {
  const controller = new AbortController();
  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    const headers = res.headers;
    let body = '';
    if (res.body) {
      const reader = res.body.getReader();
      const deadline = Date.now() + ms;
      while (Date.now() < deadline) {
        const next: any = await Promise.race([
          reader.read(),
          new Promise((resolve) =>
            setTimeout(
              () => resolve({ done: true }),
              Math.max(1, deadline - Date.now())
            )
          )
        ]);
        if (next.done) {
          break;
        }
        body += Buffer.from(next.value).toString();
      }
      try {
        controller.abort();
      } catch {
        /* ignore */
      }
      try {
        reader.releaseLock();
      } catch {
        /* ignore */
      }
    }
    return { status: res.status, headers, body };
  } catch (error: any) {
    return { status: 0, headers: new Headers(), body: `<error ${error.name}>` };
  }
};

/**
 * Collect WebSocket messages for up to `ms`.
 */
export const collectWebSocket = (url: string, ms = 1200) =>
  new Promise<string[]>((resolve) => {
    const messages: string[] = [];
    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      resolve(messages);
      return;
    }
    const finish = () => {
      try {
        socket.close();
      } catch {
        /* ignore */
      }
      resolve(messages);
    };
    socket.on('message', (data) => messages.push(data.toString()));
    socket.on('error', () => {
      /* refusal is fine */
    });
    setTimeout(finish, ms);
  });

/**
 * A winston logger whose output is captured in memory, for the runtime
 * transaction-log path.
 */
export const captureLogger = () => {
  const chunks: string[] = [];
  const sink = new Writable({
    write(chunk: any, _encoding: any, callback: any) {
      chunks.push(chunk.toString());
      callback();
    }
  });
  const logger = createLogger({
    level: 'info',
    format: logFormat.combine(logFormat.timestamp(), logFormat.json()),
    transports: [new transports.Stream({ stream: sink })]
  });
  return { logger, text: () => chunks.join('') };
};

/**
 * Mount a serverless request listener on a real HTTP server.
 */
export const serveListener = async (listener: any, port: number) => {
  const httpServer = createServer(listener);
  await new Promise<void>((resolve, reject) => {
    httpServer.once('error', reject);
    httpServer.listen(port, '127.0.0.1', () => resolve());
  });
  return {
    port,
    base: `http://127.0.0.1:${port}`,
    close: async () => {
      await new Promise<void>((resolve) => httpServer.close(() => resolve()));
    }
  };
};

/** A refusal must be a client error, not a crash and not a success. */
export const assertClientError = (status: number, label: string) =>
  assert.ok(
    status >= 400 && status < 500,
    `${label}: expected a client error, got ${status}`
  );

/** The reported name must never be echoed back to the attacker origin. */
export const assertNoCorsGrant = (acao: string | null, origin: string) =>
  assert.ok(
    acao === null || (acao !== '*' && acao !== origin),
    `a granted origin was returned for ${origin}: ${acao}`
  );

export const assertGrantsOrigin = (
  acao: string | null,
  origin: string,
  label: string
) =>
  assert.ok(
    acao === origin || acao === '*',
    `${label}: expected the configured origin or an explicit wildcard, got ${acao}`
  );

export const assertNoSecrets = (body: string, label: string) => {
  for (const [name, value] of [
    ['authorization', SECRET_AUTH],
    ['cookie', SECRET_COOKIE],
    ['x-api-key', SECRET_APIKEY],
    ['x-auth-token', SECRET_XAUTH]
  ]) {
    assert.ok(
      !body.includes(value),
      `${label}: the ${name} credential value was exposed`
    );
  }
};
