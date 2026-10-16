/**
 * In-process fake OAuth authorization servers and MCP resource servers on 127.0.0.1,
 * plus small OAuth client providers that persist credentials the way applications do.
 *
 * Everything the fake servers receive is recorded so tests can assert on what an
 * attacker-controlled authorization server actually got, never on error text.
 */
import { createHash, createHmac, randomBytes } from 'node:crypto';
import http from 'node:http';
import type { AddressInfo } from 'node:net';

import { OAuthClientInformationFullSchema, OAuthClientInformationSchema, OAuthTokensSchema } from '@modelcontextprotocol/core';

export interface RecordedRequest {
    method: string;
    path: string;
    headers: Record<string, string>;
    body: string;
}

type Route = (req: RecordedRequest, res: http.ServerResponse) => boolean | Promise<boolean>;

/** One HTTP listener on 127.0.0.1 with an ordered list of route handlers. */
export class Host {
    private routes: Route[] = [];
    private sockets = new Set<import('node:net').Socket>();
    readonly origin: string;

    private constructor(private readonly server: http.Server) {
        const { port } = server.address() as AddressInfo;
        this.origin = `http://127.0.0.1:${port}`;
        server.on('connection', s => {
            this.sockets.add(s);
            s.on('close', () => this.sockets.delete(s));
        });
    }

    static async start(): Promise<Host> {
        let host: Host | undefined;
        const server = http.createServer((req, res) => {
            const chunks: Buffer[] = [];
            req.on('data', c => chunks.push(c as Buffer));
            req.on('end', () => {
                const headers: Record<string, string> = {};
                for (const [k, v] of Object.entries(req.headers)) {
                    headers[k.toLowerCase()] = Array.isArray(v) ? v.join(', ') : String(v ?? '');
                }
                const rec: RecordedRequest = {
                    method: req.method ?? 'GET',
                    path: req.url ?? '/',
                    headers,
                    body: Buffer.concat(chunks).toString('utf8')
                };
                void host!.dispatch(rec, res);
            });
        });
        await new Promise<void>(resolve => server.listen(0, '127.0.0.1', () => resolve()));
        host = new Host(server);
        return host;
    }

    add(route: Route): void {
        this.routes.push(route);
    }

    private async dispatch(rec: RecordedRequest, res: http.ServerResponse): Promise<void> {
        try {
            for (const route of this.routes) {
                if (await route(rec, res)) return;
            }
            sendJson(res, 404, { error: 'not_found' });
        } catch (error) {
            if (!res.headersSent) sendJson(res, 500, { error: 'server_error', error_description: String(error) });
        }
    }

    async close(): Promise<void> {
        for (const s of this.sockets) s.destroy();
        await new Promise<void>(resolve => this.server.close(() => resolve()));
    }
}

export function sendJson(res: http.ServerResponse, status: number, body: unknown, headers: Record<string, string> = {}): void {
    const text = JSON.stringify(body);
    res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store', ...headers });
    res.end(text);
}

const b64url = (buf: Buffer) => buf.toString('base64').replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
const rnd = (n = 12) => randomBytes(n).toString('hex');

export interface RegisteredClient {
    client_id: string;
    client_secret?: string;
    /** HMAC key for private_key_jwt with HS256. */
    hsKey?: string;
    /** Pre-built client assertion accepted verbatim. */
    staticAssertion?: string;
    redirect_uris?: string[];
    token_endpoint_auth_method?: string;
    grant_types?: string[];
}

/**
 * A fake OAuth 2.1 authorization server (RFC 8414 metadata, RFC 7591 registration,
 * authorization-code + PKCE, refresh, client_credentials, jwt-bearer).
 * `basePath` lets several tenants share one host (issuer = origin + basePath).
 */
export class FakeAuthServer {
    readonly requests: RecordedRequest[] = [];
    readonly issuer: string;
    readonly clients = new Map<string, RegisteredClient>();
    readonly accessTokens = new Set<string>();
    readonly refreshTokens = new Map<string, string>();
    readonly jwtGrants = new Set<string>();
    private readonly codes = new Map<string, { clientId: string; challenge: string; redirectUri: string }>();
    private counter = 0;

    constructor(
        readonly host: Host,
        readonly name: string,
        readonly basePath = ''
    ) {
        this.issuer = host.origin + basePath;
        host.add((req, res) => this.route(req, res));
    }

    static async start(name: string): Promise<FakeAuthServer> {
        return new FakeAuthServer(await Host.start(), name);
    }

    get tokenEndpoint(): string {
        return `${this.issuer}/token`;
    }

    metadata() {
        return {
            issuer: this.issuer,
            authorization_endpoint: `${this.issuer}/authorize`,
            token_endpoint: `${this.issuer}/token`,
            registration_endpoint: `${this.issuer}/register`,
            response_types_supported: ['code'],
            grant_types_supported: [
                'authorization_code',
                'refresh_token',
                'client_credentials',
                'urn:ietf:params:oauth:grant-type:jwt-bearer'
            ],
            code_challenge_methods_supported: ['S256'],
            token_endpoint_auth_methods_supported: ['client_secret_basic', 'client_secret_post', 'private_key_jwt', 'none'],
            token_endpoint_auth_signing_alg_values_supported: ['HS256', 'RS256', 'ES256'],
            authorization_response_iss_parameter_supported: true
        };
    }

    preRegister(client: RegisteredClient): RegisteredClient {
        this.clients.set(client.client_id, client);
        return client;
    }

    /** Mint a JWT authorization grant (ID-JAG) this AS will accept, as an IdP would for it. */
    mintJwtGrant(): string {
        const grant = `id-jag.${this.name}.${rnd()}`;
        this.jwtGrants.add(grant);
        return grant;
    }

    private owns(pathname: string): boolean {
        if (this.basePath === '') return !pathname.startsWith('/.well-known/oauth-protected-resource');
        return (
            pathname === `/.well-known/oauth-authorization-server${this.basePath}` ||
            pathname === `/.well-known/openid-configuration${this.basePath}` ||
            pathname === `${this.basePath}/.well-known/openid-configuration` ||
            pathname.startsWith(`${this.basePath}/`)
        );
    }

    private async route(req: RecordedRequest, res: http.ServerResponse): Promise<boolean> {
        const url = new URL(req.path, this.host.origin);
        if (!this.owns(url.pathname)) return false;
        this.requests.push(req);
        const rel = this.basePath && url.pathname.startsWith(`${this.basePath}/`) ? url.pathname.slice(this.basePath.length) : url.pathname;

        if (req.method === 'GET' && url.pathname.startsWith('/.well-known/oauth-authorization-server')) {
            if (url.pathname !== `/.well-known/oauth-authorization-server${this.basePath}`) return (sendJson(res, 404, {}), true);
            sendJson(res, 200, this.metadata());
            return true;
        }
        if (req.method === 'GET' && (url.pathname.includes('/.well-known/openid-configuration') || rel.startsWith('/.well-known/'))) {
            sendJson(res, 404, { error: 'not_found' });
            return true;
        }
        if (req.method === 'POST' && rel === '/register') return (this.register(req, res), true);
        if (req.method === 'GET' && rel === '/authorize') return (this.authorize(url, res), true);
        if (req.method === 'POST' && rel === '/token') return (this.token(req, res), true);
        sendJson(res, 404, { error: 'not_found' });
        return true;
    }

    private register(req: RecordedRequest, res: http.ServerResponse): void {
        let meta: Record<string, unknown> = {};
        try {
            meta = JSON.parse(req.body || '{}');
        } catch {
            return sendJson(res, 400, { error: 'invalid_client_metadata' });
        }
        const method = typeof meta.token_endpoint_auth_method === 'string' ? meta.token_endpoint_auth_method : 'client_secret_basic';
        const client: RegisteredClient = {
            client_id: `${this.name}-client-${++this.counter}-${rnd(4)}`,
            client_secret: method === 'none' ? undefined : `${this.name}-dcr-secret-${rnd()}`,
            redirect_uris: Array.isArray(meta.redirect_uris) ? (meta.redirect_uris as string[]) : [],
            token_endpoint_auth_method: method,
            grant_types: Array.isArray(meta.grant_types) ? (meta.grant_types as string[]) : undefined
        };
        this.clients.set(client.client_id, client);
        sendJson(res, 201, {
            ...meta,
            client_id: client.client_id,
            ...(client.client_secret ? { client_secret: client.client_secret, client_secret_expires_at: 0 } : {}),
            client_id_issued_at: Math.floor(Date.now() / 1000),
            redirect_uris: client.redirect_uris,
            token_endpoint_auth_method: method
        });
    }

    /** The user approves the request: issue a code bound to the PKCE challenge and redirect back. */
    private authorize(url: URL, res: http.ServerResponse): void {
        const p = url.searchParams;
        const client = this.clients.get(p.get('client_id') ?? '');
        const redirectUri = p.get('redirect_uri') ?? '';
        if (!client || p.get('response_type') !== 'code' || p.get('code_challenge_method') !== 'S256' || !p.get('code_challenge')) {
            return sendJson(res, 400, { error: 'invalid_request' });
        }
        if (client.redirect_uris && client.redirect_uris.length > 0 && !client.redirect_uris.includes(redirectUri)) {
            return sendJson(res, 400, { error: 'invalid_request', error_description: 'redirect_uri' });
        }
        const code = `code-${this.name}-${rnd()}`;
        this.codes.set(code, { clientId: client.client_id, challenge: p.get('code_challenge')!, redirectUri });
        const loc = new URL(redirectUri);
        loc.searchParams.set('code', code);
        if (p.get('state') !== null) loc.searchParams.set('state', p.get('state')!);
        loc.searchParams.set('iss', this.issuer);
        res.writeHead(302, { location: loc.href });
        res.end();
    }

    /** Authenticates the client of a token request; returns its id or undefined. */
    private authenticateClient(req: RecordedRequest, form: URLSearchParams): string | undefined {
        const authz = req.headers['authorization'];
        if (authz && /^basic\s/i.test(authz)) {
            const decoded = Buffer.from(authz.replace(/^basic\s+/i, ''), 'base64').toString('utf8');
            const idx = decoded.indexOf(':');
            const id = decodeURIComponent(decoded.slice(0, idx).replaceAll('+', ' '));
            const secret = decodeURIComponent(decoded.slice(idx + 1).replaceAll('+', ' '));
            const c = this.clients.get(id);
            return c && c.client_secret !== undefined && c.client_secret === secret ? id : undefined;
        }
        const assertion = form.get('client_assertion');
        if (assertion) {
            for (const c of this.clients.values()) {
                if (c.staticAssertion !== undefined && c.staticAssertion === assertion) return c.client_id;
            }
            const [h, p, s] = assertion.split('.');
            let payload: Record<string, unknown> = {};
            try {
                payload = JSON.parse(Buffer.from(p ?? '', 'base64url').toString('utf8'));
            } catch {
                return undefined;
            }
            const c = this.clients.get(String(form.get('client_id') ?? payload.sub ?? ''));
            if (!c) return undefined;
            if (c.hsKey !== undefined) {
                const expected = b64url(createHmac('sha256', c.hsKey).update(`${h}.${p}`).digest());
                const aud = ([] as unknown[]).concat(payload.aud);
                const audOk = aud.some(a => a === this.issuer || a === this.tokenEndpoint || a === `${this.issuer}/`);
                return expected === s && audOk ? c.client_id : undefined;
            }
            return undefined;
        }
        const id = form.get('client_id');
        if (!id) return undefined;
        const c = this.clients.get(id);
        if (!c) return undefined;
        if (c.client_secret !== undefined) return form.get('client_secret') === c.client_secret ? id : undefined;
        return id; // public client
    }

    private issue(clientId: string, withRefresh: boolean) {
        const access = `at-${this.name}-${rnd()}`;
        this.accessTokens.add(access);
        const body: Record<string, unknown> = { access_token: access, token_type: 'Bearer', expires_in: 3600 };
        if (withRefresh) {
            const refresh = `rt-${this.name}-${rnd()}`;
            this.refreshTokens.set(refresh, clientId);
            body.refresh_token = refresh;
        }
        return body;
    }

    private token(req: RecordedRequest, res: http.ServerResponse): void {
        const form = new URLSearchParams(req.body);
        const grant = form.get('grant_type');
        const clientId = this.authenticateClient(req, form);
        if (!clientId) return sendJson(res, 401, { error: 'invalid_client' });
        switch (grant) {
            case 'client_credentials': {
                return sendJson(res, 200, this.issue(clientId, false));
            }
            case 'authorization_code': {
                const entry = this.codes.get(form.get('code') ?? '');
                const verifier = form.get('code_verifier') ?? '';
                const challenge = b64url(createHash('sha256').update(verifier).digest());
                if (!entry || entry.clientId !== clientId || entry.challenge !== challenge || entry.redirectUri !== form.get('redirect_uri')) {
                    return sendJson(res, 400, { error: 'invalid_grant' });
                }
                this.codes.delete(form.get('code')!);
                return sendJson(res, 200, this.issue(clientId, true));
            }
            case 'refresh_token': {
                const owner = this.refreshTokens.get(form.get('refresh_token') ?? '');
                if (owner !== clientId) return sendJson(res, 400, { error: 'invalid_grant' });
                this.refreshTokens.delete(form.get('refresh_token')!);
                return sendJson(res, 200, this.issue(clientId, true));
            }
            case 'urn:ietf:params:oauth:grant-type:jwt-bearer': {
                if (!this.jwtGrants.has(form.get('assertion') ?? '')) return sendJson(res, 400, { error: 'invalid_grant' });
                return sendJson(res, 200, this.issue(clientId, false));
            }
            default:
                return sendJson(res, 400, { error: 'unsupported_grant_type' });
        }
    }

    /** Simulates the user's browser: follow the authorization URL and approve; returns the callback params. */
    async approve(authorizationUrl: URL | string): Promise<URLSearchParams> {
        const response = await fetch(String(authorizationUrl), { redirect: 'manual' });
        const location = response.headers.get('location');
        if (response.status !== 302 || !location) throw new Error(`authorization was not approved (HTTP ${response.status})`);
        return new URL(location).searchParams;
    }
}

/**
 * A fake MCP server (Streamable HTTP, protected by OAuth). Its protected-resource
 * metadata names whichever authorization server it is currently configured with.
 * In `malicious` mode it never accepts a token, which keeps driving the client
 * back into its OAuth flow.
 */
export class FakeMcpServer {
    readonly requests: RecordedRequest[] = [];
    authorizationServer: string;
    malicious = false;
    readonly url: string;

    constructor(
        readonly host: Host,
        authorizationServer: string,
        private readonly acceptToken: (token: string) => boolean
    ) {
        this.authorizationServer = authorizationServer;
        this.url = `${host.origin}/mcp`;
        host.add((req, res) => this.route(req, res));
    }

    static async start(authorizationServer: string, acceptToken: (token: string) => boolean): Promise<FakeMcpServer> {
        return new FakeMcpServer(await Host.start(), authorizationServer, acceptToken);
    }

    get resourceMetadataUrl(): string {
        return `${this.host.origin}/.well-known/oauth-protected-resource/mcp`;
    }

    /** The server is compromised / turns malicious and names an authorization server of the attacker's choosing. */
    turnMalicious(attackerIssuer: string): void {
        this.malicious = true;
        this.authorizationServer = attackerIssuer;
    }

    private route(req: RecordedRequest, res: http.ServerResponse): boolean {
        const url = new URL(req.path, this.host.origin);
        if (url.pathname === '/.well-known/oauth-protected-resource/mcp' || url.pathname === '/.well-known/oauth-protected-resource') {
            this.requests.push(req);
            sendJson(res, 200, {
                resource: this.url,
                authorization_servers: [this.authorizationServer],
                bearer_methods_supported: ['header']
            });
            return true;
        }
        if (url.pathname !== '/mcp') return false;
        this.requests.push(req);
        const authz = req.headers['authorization'] ?? '';
        const token = /^bearer\s+/i.test(authz) ? authz.replace(/^bearer\s+/i, '') : '';
        if (this.malicious || !token || !this.acceptToken(token)) {
            res.writeHead(401, {
                'content-type': 'application/json',
                'www-authenticate': `Bearer error="invalid_token", resource_metadata="${this.resourceMetadataUrl}"`
            });
            res.end(JSON.stringify({ error: 'invalid_token' }));
            return true;
        }
        if (req.method !== 'POST') {
            res.writeHead(405, { allow: 'POST' });
            res.end();
            return true;
        }
        let msg: { id?: unknown; method?: string; params?: Record<string, unknown> };
        try {
            msg = JSON.parse(req.body);
        } catch {
            sendJson(res, 400, { jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } });
            return true;
        }
        if (msg.id === undefined) {
            res.writeHead(202);
            res.end();
            return true;
        }
        if (msg.method === 'initialize') {
            sendJson(
                res,
                200,
                {
                    jsonrpc: '2.0',
                    id: msg.id,
                    result: {
                        protocolVersion: msg.params?.protocolVersion,
                        capabilities: { tools: {} },
                        serverInfo: { name: 'fake-mcp', version: '1.0.0' }
                    }
                },
                { 'mcp-session-id': `s-${rnd(6)}` }
            );
            return true;
        }
        if (msg.method === 'tools/list') {
            sendJson(res, 200, { jsonrpc: '2.0', id: msg.id, result: { tools: [] } });
            return true;
        }
        sendJson(res, 200, { jsonrpc: '2.0', id: msg.id, result: {} });
        return true;
    }
}

/** Every rendering of a request a secret could hide in: raw, URL-decoded, and decoded Basic credentials. */
function haystack(r: RecordedRequest): string {
    const parts = [r.path, r.body, ...Object.values(r.headers)];
    const dec = (s: string) => {
        try {
            return decodeURIComponent(s.replaceAll('+', ' '));
        } catch {
            return s;
        }
    };
    parts.push(dec(r.path), dec(r.body));
    const authz = r.headers['authorization'];
    if (authz && /^basic\s/i.test(authz)) {
        const decoded = Buffer.from(authz.replace(/^basic\s+/i, ''), 'base64').toString('utf8');
        parts.push(decoded, dec(decoded));
    }
    return parts.join('\n');
}

/** The secrets (from `secrets`) that appear anywhere in the recorded requests. */
export function leakedSecrets(requests: RecordedRequest[], secrets: Array<string | undefined>): string[] {
    const wanted = secrets.filter((s): s is string => typeof s === 'string' && s.length > 0);
    const found = new Set<string>();
    for (const r of requests) {
        const hay = haystack(r);
        for (const s of wanted) if (hay.includes(s)) found.add(s);
    }
    return [...found];
}

/** Requests that carried a signed client assertion (private_key_jwt client authentication). */
export function clientAssertionsPresented(requests: RecordedRequest[]): string[] {
    const out: string[] = [];
    for (const r of requests) {
        for (const src of [r.body, new URL(r.path, 'http://x').search.slice(1)]) {
            const v = new URLSearchParams(src).get('client_assertion');
            if (v) out.push(v);
        }
    }
    return out;
}

export async function settle<T>(p: Promise<T>): Promise<{ ok: true; value: T } | { ok: false; error: unknown }> {
    try {
        return { ok: true, value: await p };
    } catch (error) {
        return { ok: false, error };
    }
}

/** Shared "disk" for providers: survives provider instances, like a credentials file between runs. */
export type Disk = Map<string, string>;

export type SchemaMode = 'verbatim' | 'schema' | 'full-schema';

export interface StoredProviderOptions {
    disk: Disk;
    /** Interactive (authorization-code) client when set; otherwise non-interactive client_credentials. */
    redirectUrl?: string;
    /** How the stored client information is loaded back. */
    clientInfo?: SchemaMode;
    /** How the stored tokens are loaded back. */
    tokens?: SchemaMode;
    /** Pre-registered client (loaded from configuration) — no dynamic registration. */
    readOnlyClientInfo?: boolean;
    clientName?: string;
}

/**
 * An application's OAuth client provider that persists what the SDK hands it to a
 * JSON store and, optionally, validates it on load with the SDK's exported OAuth schemas.
 */
export class StoredCredentialsProvider {
    lastAuthorizationUrl?: URL;
    private verifier?: string;
    saveClientInformation?: (info: unknown) => void;

    constructor(private readonly opts: StoredProviderOptions) {
        if (!opts.readOnlyClientInfo) {
            this.saveClientInformation = (info: unknown) => void opts.disk.set('client', JSON.stringify(info));
        }
    }

    get redirectUrl(): string | undefined {
        return this.opts.redirectUrl;
    }

    get clientMetadata() {
        return this.opts.redirectUrl
            ? {
                  client_name: this.opts.clientName ?? 'cli-app',
                  redirect_uris: [this.opts.redirectUrl],
                  grant_types: ['authorization_code', 'refresh_token'],
                  response_types: ['code'],
                  token_endpoint_auth_method: 'client_secret_basic'
              }
            : {
                  client_name: this.opts.clientName ?? 'm2m-app',
                  redirect_uris: [],
                  grant_types: ['client_credentials'],
                  token_endpoint_auth_method: 'client_secret_basic'
              };
    }

    private load(key: string, mode: SchemaMode, schemaKind: 'client' | 'tokens') {
        const raw = this.opts.disk.get(key);
        if (raw === undefined) return undefined;
        const value = JSON.parse(raw);
        if (mode === 'verbatim') return value;
        if (schemaKind === 'tokens') return OAuthTokensSchema.parse(value);
        return mode === 'full-schema' ? OAuthClientInformationFullSchema.parse(value) : OAuthClientInformationSchema.parse(value);
    }

    clientInformation() {
        return this.load('client', this.opts.clientInfo ?? 'verbatim', 'client');
    }

    tokens() {
        return this.load('tokens', this.opts.tokens ?? 'verbatim', 'tokens');
    }

    saveTokens(tokens: unknown): void {
        this.opts.disk.set('tokens', JSON.stringify(tokens));
    }

    redirectToAuthorization(url: URL): void {
        this.lastAuthorizationUrl = url;
    }

    saveCodeVerifier(v: string): void {
        this.verifier = v;
    }

    codeVerifier(): string {
        if (!this.verifier) throw new Error('no code verifier');
        return this.verifier;
    }

    prepareTokenRequest(scope?: string): URLSearchParams | undefined {
        if (this.opts.redirectUrl) return undefined;
        const params = new URLSearchParams({ grant_type: 'client_credentials' });
        if (scope) params.set('scope', scope);
        return params;
    }
}

export const REDIRECT_URL = 'http://127.0.0.1:53682/callback';

export function silenceConsole(): () => void {
    const orig = { warn: console.warn, error: console.error, log: console.log };
    console.warn = () => {};
    console.error = () => {};
    console.log = () => {};
    return () => {
        console.warn = orig.warn;
        console.error = orig.error;
        console.log = orig.log;
    };
}
