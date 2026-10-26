/**
 * Shared verifier helpers: local canaries that record whether anything actually connected to an
 * internal address, and small builders for requests the product accepts.
 */
import http from 'node:http';
import net from 'node:net';

export interface Canary {
  port: number;
  readonly hits: string[];
  close(): Promise<void>;
}

export interface CanaryOptions {
  body?: unknown;
  contentType?: string;
  host?: string;
  status?: number;
}

export async function startCanary(options: CanaryOptions = {}): Promise<Canary> {
  const { body = { ok: true }, contentType = 'application/json', host = '127.0.0.1', status = 200 } =
    options;
  const hits: string[] = [];
  const server = http.createServer((req, res) => {
    hits.push(`${req.method} ${req.url}`);
    res.setHeader('content-type', contentType);
    res.statusCode = status;
    res.end(typeof body === 'string' ? body : JSON.stringify(body));
  });

  await new Promise<void>((resolve) => server.listen(0, host, () => resolve()));
  const port = (server.address() as net.AddressInfo).port;

  return {
    port,
    get hits() {
      return hits;
    },
    close: () => new Promise<void>((resolve) => server.close(() => resolve())),
  };
}

/** The unverified client-held credential format the product decodes itself. */
export const clientToken = (payload: Record<string, unknown>): string =>
  `http_nosafe.${Buffer.from(JSON.stringify(payload)).toString('base64')}`;

export const isClientError = (status: number): boolean => status >= 400 && status < 500;

export interface RecordedFetch {
  calls: Array<{ url: string; init?: RequestInit }>;
  restore(): void;
}

/**
 * Installs an emulated network for the legitimate-use checks: public destinations answer, and a
 * redirect is returned only when the caller asked for manual handling, so both automatic and
 * per-hop redirect following are exercised.
 */
export function emulateNetwork(
  routes: Record<string, (init?: RequestInit) => Response>,
): RecordedFetch {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const original = globalThis.fetch;

  const fake = async (input: any, init?: RequestInit): Promise<Response> => {
    const url = typeof input === 'string' ? input : String(input?.url ?? input);
    calls.push({ init, url });

    const handler = routes[url];
    if (handler) {
      const response = handler(init);
      if (response instanceof Response) return response;
    }

    return new Response(JSON.stringify({ ok: true }), {
      headers: { 'content-type': 'application/json' },
      status: 200,
    });
  };

  globalThis.fetch = fake as typeof fetch;

  return {
    calls,
    restore: () => {
      globalThis.fetch = original;
    },
  };
}

/** A public destination that no test can accidentally turn into a local one. */
export const PUBLIC_URL = 'http://8.8.8.8/resource';
export const PUBLIC_URL_2 = 'http://8.8.4.4/resource';
