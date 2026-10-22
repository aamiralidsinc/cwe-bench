import http from 'node:http';
import net from 'node:net';
import os from 'node:os';
import { createRequire } from 'node:module';
import { RsdoctorSDK } from '/workspace/packages/sdk/dist/index.js';

const requireFromSdk = createRequire('/workspace/packages/sdk/package.json');

export const WebSocket = requireFromSdk('ws') as any;

export interface HttpResponse {
  status: number;
  headers: http.IncomingHttpHeaders;
  body: string;
}

export interface HttpOutcome {
  result?: HttpResponse;
  error?: string;
}

export interface Started {
  sdk: any;
  port: number;
  origin: string;
}

export function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      const port = typeof address === 'object' && address ? address.port : 0;
      server.close(() => resolve(port));
    });
  });
}

export function lanIPv4(): string | undefined {
  for (const list of Object.values(os.networkInterfaces())) {
    for (const item of list || []) {
      if (item.family === 'IPv4' && !item.internal) {
        return item.address;
      }
    }
  }
  return undefined;
}

export interface RequestOptions {
  port: number;
  path: string;
  method?: string;
  hostname?: string;
  headers?: Record<string, string | number>;
  body?: string;
}

export function tryHttp(options: RequestOptions): Promise<HttpOutcome> {
  return new Promise((resolve) => {
    const req = http.request(
      {
        hostname: options.hostname ?? '127.0.0.1',
        port: options.port,
        path: options.path,
        method: options.method ?? 'GET',
        headers: options.headers,
        agent: false,
        timeout: 8000,
      },
      (res) => {
        let body = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => {
          body += chunk;
        });
        res.on('end', () => {
          resolve({
            result: {
              status: res.statusCode ?? 0,
              headers: res.headers,
              body,
            },
          });
        });
      },
    );
    req.on('timeout', () => {
      req.destroy(new Error('timeout'));
    });
    req.on('error', (error: NodeJS.ErrnoException) => {
      resolve({ error: error.code || error.message });
    });
    if (options.body !== undefined) {
      req.write(options.body);
    }
    req.end();
  });
}

export async function httpRequest(options: RequestOptions): Promise<HttpResponse> {
  const outcome = await tryHttp(options);
  if (!outcome.result) {
    throw new Error(`request failed: ${outcome.error}`);
  }
  return outcome.result;
}

export interface StartOptions {
  server?: Record<string, unknown>;
  noServer?: boolean;
  port?: number;
}

export async function startSdk(options: StartOptions = {}): Promise<Started> {
  process.setMaxListeners(0);
  const port = options.port ?? (await freePort());
  const sdk = new RsdoctorSDK({
    name: 'hidden-test',
    root: '/workspace',
    config: {
      ...(options.noServer ? { noServer: true } : {}),
      server: {
        port,
        ...(options.server ?? {}),
      },
    },
  });
  await sdk.bootstrap();
  return { sdk, port: sdk.server.port, origin: sdk.server.origin };
}

export async function disposeSdk(sdk: any): Promise<void> {
  if (!sdk) {
    return;
  }
  try {
    await sdk.dispose();
  } catch {
    // a server that never started must not fail the test cleanup
  }
}

export interface WsOutcome {
  opened: boolean;
  error?: string;
  ws?: any;
}

export function connectWs(
  url: string,
  headers?: Record<string, string>,
): Promise<WsOutcome> {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (value: WsOutcome) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      resolve(value);
    };
    const ws = new WebSocket(url, {
      headers,
      handshakeTimeout: 6000,
    });
    const timer = setTimeout(() => {
      try {
        ws.terminate();
      } catch {
        // ignore
      }
      finish({ opened: false, error: 'timeout' });
    }, 8000);
    ws.on('open', () => finish({ opened: true, ws }));
    ws.on('error', (error: Error) => finish({ opened: false, error: error.message }));
    ws.on('unexpected-response', (_req: unknown, res: any) =>
      finish({ opened: false, error: `status ${res.statusCode}` }),
    );
  });
}

export function closeWs(ws: any): void {
  try {
    ws.close();
  } catch {
    // ignore
  }
}

export function readWsMessage(ws: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('ws message timeout')), 6000);
    ws.once('message', (raw: any) => {
      clearTimeout(timer);
      try {
        resolve(JSON.parse(raw.toString()));
      } catch (error) {
        reject(error);
      }
    });
  });
}

/** One HTTP/1.0 exchange over a raw socket, so the request can omit the Host header. */
export function rawHttpRequest(port: number, payload: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const socket = net.connect(port, '127.0.0.1');
    let data = '';
    const timer = setTimeout(() => {
      socket.destroy();
      resolve(data);
    }, 5000);
    socket.on('connect', () => socket.write(payload));
    socket.on('data', (chunk) => {
      data += chunk.toString('utf8');
    });
    socket.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    socket.on('close', () => {
      clearTimeout(timer);
      resolve(data);
    });
  });
}

export function statusOf(raw: string): number {
  const match = /^HTTP\/1\.[01] (\d{3})/.exec(raw);
  return match ? Number(match[1]) : 0;
}

export function tokenOf(url: string): string {
  try {
    return new URL(url).searchParams.get('token') ?? '';
  } catch {
    return '';
  }
}

export function wsUrlFor(port: number, query = ''): string {
  return `ws://127.0.0.1:${port}/${query}`;
}
