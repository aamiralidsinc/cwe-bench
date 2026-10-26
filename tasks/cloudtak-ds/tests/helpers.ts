/**
 * Shared harness: the product's real route handlers, a per-resource auth stub,
 * an in-memory basemap store, and loopback canaries that record whether
 * anything actually connected.
 */
import http from 'node:http';
import net from 'node:net';
import { randomUUID } from 'node:crypto';
import { AuthUser, AuthUserAccess } from '../lib/auth.js';
import Auth from '../lib/auth.js';
import router from '../routes/basemap.js';

export interface Res {
    code: number;
    headersSent: boolean;
    body: any;
    headers: Record<string, string>;
}

export interface Canary {
    port: number;
    origin: string;
    marker: string;
    readonly hits: number;
    readonly paths: string[];
    close(): Promise<void>;
}

const sockets = new Set<net.Socket>();

function track(server: http.Server): void {
    server.on('connection', (socket) => {
        sockets.add(socket);
        socket.on('close', () => sockets.delete(socket));
    });
}

async function closeServer(server: http.Server): Promise<void> {
    await new Promise<void>((resolve) => server.close(() => resolve()));
    for (const socket of sockets) socket.destroy();
}

/** A loopback service that records every connection it receives. */
export async function startCanary(): Promise<Canary> {
    let hits = 0;
    const paths: string[] = [];
    const marker = `INTERNAL-${randomUUID()}`;

    const server = http.createServer((req, res) => {
        hits += 1;
        paths.push(`${req.method} ${req.url}`);
        res.setHeader('content-type', 'application/json');
        res.end(JSON.stringify({
            name: marker,
            attribution: marker,
            description: marker,
            tilejson: '3.0.0',
            tiles: [`http://127.0.0.1:1/tiles/{z}/{x}/{y}.png`],
        }));
    });
    track(server);
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', () => resolve()));
    const port = (server.address() as net.AddressInfo).port;

    return {
        port,
        origin: `http://127.0.0.1:${port}`,
        marker,
        get hits() {
            return hits;
        },
        get paths() {
            return paths;
        },
        close: () => closeServer(server),
    };
}

export interface TileServer {
    port: number;
    origin: string;
    readonly requests: string[];
    close(): Promise<void>;
}

export interface TileRoutes {
    /** TileJSON returned for a path (default `/tilejson.json`). */
    tilejson?: Record<string, unknown>;
    /** A path that answers with a 302 to the given location. */
    redirectFrom?: string;
    redirectTo?: string;
}

/** The operator-configured tile service, reachable only by its configured origin. */
export async function startTileServer(routes: TileRoutes = {}): Promise<TileServer> {
    const requests: string[] = [];
    const body = routes.tilejson ?? {
        tilejson: '3.0.0',
        name: 'CONFIGURED-TILEJSON',
        tiles: ['http://127.0.0.1:1/tiles/{z}/{x}/{y}.png'],
    };

    const server = http.createServer((req, res) => {
        requests.push(String(req.url));
        if (routes.redirectFrom && req.url && req.url.split('?')[0] === routes.redirectFrom) {
            res.writeHead(302, { location: routes.redirectTo ?? 'http://127.0.0.1:1/nowhere' });
            res.end();
            return;
        }
        res.setHeader('content-type', 'application/json');
        res.end(JSON.stringify(body));
    });
    track(server);
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', () => resolve()));
    const port = (server.address() as net.AddressInfo).port;

    return {
        port,
        origin: `http://tiles.internal.test:${port}`,
        get requests() {
            return requests;
        },
        close: () => closeServer(server),
    };
}

export function setUser(access: AuthUserAccess = AuthUserAccess.ADMIN, email = 'user@example.com'): void {
    (Auth as any).is_auth = async () => new AuthUser(access, email, 'test-token');
}

export class BasemapStore {
    next = 1;
    rows = new Map<number, Record<string, any>>();

    add(row: Record<string, any>): Record<string, any> {
        const id = this.next++;
        const full = {
            id,
            name: 'test-basemap',
            protocol: 'zxy',
            type: 'raster',
            format: 'png',
            scheme: 'xyz',
            minzoom: 0,
            maxzoom: 16,
            tilesize: 256,
            username: 'user@example.com',
            sharing_enabled: false,
            sharing_token: null,
            hidden: false,
            overlay: false,
            attribution: null,
            collection: null,
            frequency: null,
            bounds: undefined,
            center: undefined,
            tilejson: null,
            ...row,
        };
        this.rows.set(id, full);
        return full;
    }

    get models(): Record<string, any> {
        return {
            Basemap: {
                from: async (id: number | string) => {
                    const row = this.rows.get(Number(id));
                    if (!row) throw new Error('basemap not found');
                    return row;
                },
                generate: async (row: Record<string, any>) => this.add(row),
                commit: async (id: number | string, row: Record<string, any>) => {
                    const current = this.rows.get(Number(id));
                    if (!current) throw new Error('basemap not found');
                    this.rows.set(Number(id), { ...current, ...row });
                    return this.rows.get(Number(id));
                },
                delete: async (id: number | string) => {
                    this.rows.delete(Number(id));
                },
            },
            Setting: {
                typed: async () => ({ value: -1 }),
            },
        };
    }
}

export function makeConfig(store: BasemapStore, tiles: TileServer, overrides: Record<string, any> = {}): any {
    return {
        StackName: 'prod',
        API_URL: 'http://localhost:5001',
        PMTILES_URL: tiles.origin,
        SigningSecret: 'coe-wildland-fire',
        models: store.models,
        server: {},
        user: undefined,
        ...overrides,
    };
}

const METHODS = ['get', 'post', 'put', 'patch', 'delete'] as const;

export type Handlers = Record<string, (req: any, res: any) => Promise<void>>;

/** Register the product's real basemap routes and return the handlers by `METHOD path`. */
export async function loadRoutes(config: any): Promise<Handlers> {
    const handlers: Handlers = {};
    const schema: any = {};
    for (const method of METHODS) {
        schema[method] = (path: string, _opts: unknown, handler: (req: any, res: any) => Promise<void>) => {
            handlers[`${method.toUpperCase()} ${path}`] = handler;
        };
    }
    await router(schema, config);
    return handlers;
}

export function makeRequest(opts: {
    params?: Record<string, string>;
    query?: Record<string, any>;
    body?: any;
    headers?: Record<string, string>;
} = {}): any {
    const headers = opts.headers ?? {};
    return {
        params: opts.params ?? {},
        query: opts.query ?? {},
        body: opts.body,
        headers,
        header(name: string) {
            return headers[name.toLowerCase()];
        },
        pipe() {
            /* multipart uploads are not used by these suites */
        },
    };
}

export function makeResponse(): Res {
    const res: any = {
        code: 0,
        headersSent: false,
        body: undefined,
        headers: {},
        status(code: number) {
            res.code = code;
            return res;
        },
        send(body: any) {
            res.body = body;
            res.headersSent = true;
            return res;
        },
        json(body: any) {
            res.body = body;
            res.headersSent = true;
            if (!res.code) res.code = 200;
            return res;
        },
        setHeader(name: string, value: string) {
            res.headers[name.toLowerCase()] = value;
            return res;
        },
        writeHead(code: number, headers?: Record<string, string>) {
            res.code = code;
            Object.assign(res.headers, headers ?? {});
            res.headersSent = true;
            return res;
        },
        write() {
            return true;
        },
        end() {
            return res;
        },
    };
    return res as Res;
}

export async function call(handlers: Handlers, method: string, path: string, req: any): Promise<Res> {
    const handler = handlers[`${method} ${path}`];
    if (!handler) throw new Error(`route not registered: ${method} ${path}`);
    const res = makeResponse();
    await handler(req, res);
    return res;
}

export function isClientError(res: Res): boolean {
    return res.code >= 400 && res.code < 500;
}

export function bodyText(res: Res): string {
    try {
        return JSON.stringify(res.body);
    } catch {
        return String(res.body);
    }
}
