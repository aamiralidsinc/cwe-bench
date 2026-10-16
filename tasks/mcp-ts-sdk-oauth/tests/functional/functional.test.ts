/**
 * Functional tests: legitimate OAuth use against the authorization server the MCP
 * server (honestly) names keeps working end to end — client credentials, signed
 * assertions, cross-app access, interactive sign-in with refresh, dynamic registration
 * reuse, and applications that validate their stored credentials with the SDK schemas.
 *
 * Ported from Hadi's task (2026-10-15); the last group was added for the cwe-bench version
 * (2026-10-16).
 */
import { randomBytes } from 'node:crypto';

import {
    auth,
    Client,
    ClientCredentialsProvider,
    CrossAppAccessProvider,
    discoverOAuthServerInfo,
    exchangeAuthorization,
    fetchToken,
    PrivateKeyJwtProvider,
    refreshAuthorization,
    startAuthorization,
    StaticPrivateKeyJwtProvider,
    StreamableHTTPClientTransport,
    withOAuth
} from '@modelcontextprotocol/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import type { Disk } from '../support/harness';
import {
    FakeAuthServer,
    FakeMcpServer,
    Host,
    leakedSecrets,
    REDIRECT_URL,
    settle,
    silenceConsole,
    StoredCredentialsProvider
} from '../support/harness';

const rnd = () => randomBytes(10).toString('hex');

let legit: FakeAuthServer;
let mcp: FakeMcpServer;
let extraHosts: Host[];
let restoreConsole: () => void;

beforeEach(async () => {
    restoreConsole = silenceConsole();
    extraHosts = [];
    legit = await FakeAuthServer.start('legit');
    mcp = await FakeMcpServer.start(legit.issuer, t => legit.accessTokens.has(t));
});

afterEach(async () => {
    restoreConsole();
    await Promise.all([legit.host.close(), mcp.host.close(), ...extraHosts.map(h => h.close())]);
});

async function connectAndListTools(provider: unknown): Promise<void> {
    const client = new Client({ name: 'app', version: '1.0.0' });
    const transport = new StreamableHTTPClientTransport(new URL(mcp.url), { authProvider: provider as never });
    await client.connect(transport);
    const tools = await client.listTools();
    expect(Array.isArray(tools.tools)).toBe(true);
    await client.close();
}

function tokenGrants(as: FakeAuthServer): string[] {
    return as.requests.filter(r => r.method === 'POST' && r.path.endsWith('/token')).map(r => new URLSearchParams(r.body).get('grant_type') ?? '');
}

function registrations(as: FakeAuthServer): number {
    return as.requests.filter(r => r.method === 'POST' && r.path.endsWith('/register')).length;
}

describe('legitimate OAuth flows against the authorization server the MCP server names', () => {
    it('client credentials (pinned issuer) through the transport: connects and calls the server', async () => {
        const secret = `secret-${rnd()}`;
        legit.preRegister({ client_id: 'reporting-job', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'reporting-job', clientSecret: secret, expectedIssuer: legit.issuer });

        await connectAndListTools(provider);
        expect(tokenGrants(legit)).toContain('client_credentials');
        expect(provider.tokens()?.access_token && legit.accessTokens.has(provider.tokens()!.access_token)).toBe(true);
    });

    it('client credentials: an issuer configured with a trailing slash still matches its authorization server', async () => {
        const secret = `secret-${rnd()}`;
        legit.preRegister({ client_id: 'job', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'job', clientSecret: secret, expectedIssuer: `${legit.issuer}/` });

        await connectAndListTools(provider);
        expect(tokenGrants(legit)).toContain('client_credentials');
    });

    it('client credentials without a pinned issuer keeps working with an honest server', async () => {
        const secret = `secret-${rnd()}`;
        legit.preRegister({ client_id: 'legacy-job', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'legacy-job', clientSecret: secret });

        await connectAndListTools(provider);
        expect(tokenGrants(legit)).toContain('client_credentials');
    });

    it('standalone token helper: client credentials against the discovered legitimate server returns a usable token', async () => {
        const secret = `secret-${rnd()}`;
        legit.preRegister({ client_id: 'job', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'job', clientSecret: secret, expectedIssuer: legit.issuer });

        const info = await discoverOAuthServerInfo(mcp.url);
        const tokens = await fetchToken(provider, info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata,
            resource: new URL(mcp.url)
        });
        expect(legit.accessTokens.has(tokens.access_token)).toBe(true);
    });

    it('standalone token helper: private_key_jwt (HS256) against the legitimate server', async () => {
        const key = `hs256-key-${rnd()}-${rnd()}-${rnd()}`;
        legit.preRegister({ client_id: 'signer', hsKey: key });
        const provider = new PrivateKeyJwtProvider({ clientId: 'signer', privateKey: key, algorithm: 'HS256', expectedIssuer: legit.issuer });

        const info = await discoverOAuthServerInfo(mcp.url);
        const tokens = await fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata });
        expect(legit.accessTokens.has(tokens.access_token)).toBe(true);
    });

    it('standalone token helper: a client registered in an earlier run is reused against the same server', async () => {
        const disk: Disk = new Map();
        expect(await auth(new StoredCredentialsProvider({ disk }) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');

        const info = await discoverOAuthServerInfo(mcp.url);
        const tokens = await fetchToken(new StoredCredentialsProvider({ disk }) as never, info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata
        });
        expect(legit.accessTokens.has(tokens.access_token)).toBe(true);
        expect(registrations(legit)).toBe(1);
    });

    it('static private_key_jwt through auth()', async () => {
        const assertion = `eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzdGF0aWMifQ.${rnd()}`;
        legit.preRegister({ client_id: 'static-client', staticAssertion: assertion });
        const provider = new StaticPrivateKeyJwtProvider({ clientId: 'static-client', jwtBearerAssertion: assertion, expectedIssuer: legit.issuer });

        expect(await auth(provider, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(legit.accessTokens.has(provider.tokens()!.access_token)).toBe(true);
    });

    it('cross-app access (jwt-bearer) through auth()', async () => {
        const secret = `xaa-secret-${rnd()}`;
        legit.preRegister({ client_id: 'xaa-client', client_secret: secret });
        const audiences: string[] = [];
        const provider = new CrossAppAccessProvider({
            assertion: async ctx => {
                audiences.push(ctx.authorizationServerUrl);
                return legit.mintJwtGrant();
            },
            clientId: 'xaa-client',
            clientSecret: secret,
            expectedIssuer: legit.issuer
        });

        expect(await auth(provider, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(tokenGrants(legit)).toContain('urn:ietf:params:oauth:grant-type:jwt-bearer');
        expect(audiences.length).toBe(1);
    });

    it('multi-tenant identity provider: a client pinned to its tenant gets tokens from that tenant', async () => {
        const idp = await Host.start();
        extraHosts.push(idp);
        const acme = new FakeAuthServer(idp, 'acme', '/realms/acme');
        new FakeAuthServer(idp, 'other', '/realms/acme-support');
        const secret = `tenant-secret-${rnd()}`;
        acme.preRegister({ client_id: 'svc', client_secret: secret });
        mcp.authorizationServer = acme.issuer;
        const provider = new ClientCredentialsProvider({ clientId: 'svc', clientSecret: secret, expectedIssuer: acme.issuer });

        const info = await discoverOAuthServerInfo(mcp.url);
        const tokens = await fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata });
        expect(acme.accessTokens.has(tokens.access_token)).toBe(true);
    });

    it('interactive sign-in through the transport, then a later refresh at the same server', async () => {
        const disk: Disk = new Map();
        const provider = new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL });
        const client = new Client({ name: 'app', version: '1.0.0' });
        const transport = new StreamableHTTPClientTransport(new URL(mcp.url), { authProvider: provider as never });
        expect((await settle(client.connect(transport))).ok).toBe(false);
        expect(provider.lastAuthorizationUrl?.href.startsWith(`${legit.issuer}/authorize`)).toBe(true);
        await transport.finishAuth(await legit.approve(provider.lastAuthorizationUrl!));
        await settle(client.close());

        await connectAndListTools(provider);
        expect(tokenGrants(legit)).toEqual(['authorization_code']);

        expect(await auth(new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL }) as never, { serverUrl: mcp.url })).toBe(
            'AUTHORIZED'
        );
        expect(tokenGrants(legit)).toEqual(['authorization_code', 'refresh_token']);
        expect(registrations(legit)).toBe(1);
    });

    it('stored credentials validated with the SDK schemas: sign-in, then a later run refreshes at the same server without re-registering', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL, clientInfo: 'schema', tokens: 'schema' } as const;
        const provider = new StoredCredentialsProvider(opts);
        expect(await auth(provider as never, { serverUrl: mcp.url })).toBe('REDIRECT');
        const callback = await legit.approve(provider.lastAuthorizationUrl!);
        expect(
            await auth(provider as never, { serverUrl: mcp.url, authorizationCode: callback.get('code')!, iss: callback.get('iss') ?? undefined })
        ).toBe('AUTHORIZED');

        const later = new StoredCredentialsProvider(opts);
        expect(await auth(later as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(tokenGrants(legit)).toEqual(['authorization_code', 'refresh_token']);
        expect(registrations(legit)).toBe(1);
        await connectAndListTools(new StoredCredentialsProvider(opts));
    });

    it('registered machine client validated with the client-information schema is reused on later runs', async () => {
        const disk: Disk = new Map();
        const opts = { disk, clientInfo: 'schema', tokens: 'schema' } as const;
        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        await connectAndListTools(new StoredCredentialsProvider(opts));
        expect(registrations(legit)).toBe(1);
        expect(tokenGrants(legit).filter(g => g === 'client_credentials').length).toBeGreaterThanOrEqual(2);
    });

    it('pre-registered credentials saved with their issuer and validated with the schema work through the transport', async () => {
        const secret = `prereg-secret-${rnd()}`;
        legit.preRegister({ client_id: 'svc-account', client_secret: secret });
        const disk: Disk = new Map([['client', JSON.stringify({ client_id: 'svc-account', client_secret: secret, issuer: legit.issuer })]]);

        await connectAndListTools(new StoredCredentialsProvider({ disk, clientInfo: 'schema', readOnlyClientInfo: true }));
        expect(tokenGrants(legit)).toContain('client_credentials');
    });

    it('withOAuth() middleware with a registered client validated with the full client-information schema', async () => {
        const disk: Disk = new Map();
        const opts = { disk, clientInfo: 'full-schema' } as const;
        const init = {
            method: 'POST',
            headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream' },
            body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} })
        };
        const first = await withOAuth(new StoredCredentialsProvider(opts) as never, mcp.url)(fetch)(mcp.url, init);
        expect(first.status).toBe(200);
        disk.delete('tokens');
        const second = await withOAuth(new StoredCredentialsProvider(opts) as never, mcp.url)(fetch)(mcp.url, init);
        expect(second.status).toBe(200);
        expect(registrations(legit)).toBe(1);
    });
});

/** An earlier interactive sign-in through auth(): registers, the user approves, the code is redeemed. */
async function signIn(provider: StoredCredentialsProvider, serverUrl: string = mcp.url): Promise<void> {
    expect(await auth(provider as never, { serverUrl })).toBe('REDIRECT');
    const callback = await legit.approve(provider.lastAuthorizationUrl!);
    expect(
        await auth(provider as never, { serverUrl, authorizationCode: callback.get('code')!, iss: callback.get('iss') ?? undefined })
    ).toBe('AUTHORIZED');
}

describe('saved credentials used with the standalone helpers against the same authorization server', () => {
    it('refresh helper: saved credentials refresh at the authorization server they came from', async () => {
        const disk: Disk = new Map();
        await signIn(new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL }));
        const info = await discoverOAuthServerInfo(mcp.url);
        const refreshed = await refreshAuthorization(info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata,
            clientInformation: JSON.parse(disk.get('client')!),
            refreshToken: JSON.parse(disk.get('tokens')!).refresh_token
        });
        expect(legit.accessTokens.has(refreshed.access_token)).toBe(true);
        expect(tokenGrants(legit)).toEqual(['authorization_code', 'refresh_token']);
    });

    it('refresh helper: given only the authorization server URL (no metadata) it still refreshes there', async () => {
        const disk: Disk = new Map();
        await signIn(new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL }));
        const refreshed = await refreshAuthorization(new URL(legit.issuer), {
            clientInformation: JSON.parse(disk.get('client')!),
            refreshToken: JSON.parse(disk.get('tokens')!).refresh_token
        });
        expect(legit.accessTokens.has(refreshed.access_token)).toBe(true);
    });

    it('code-exchange helper: an application-driven authorization-code flow with the saved registration', async () => {
        const disk: Disk = new Map();
        const provider = new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL });
        expect(await auth(provider as never, { serverUrl: mcp.url })).toBe('REDIRECT');
        const info = await discoverOAuthServerInfo(mcp.url);
        const clientInformation = JSON.parse(disk.get('client')!);
        const { authorizationUrl, codeVerifier } = await startAuthorization(info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata,
            clientInformation,
            redirectUrl: REDIRECT_URL
        });
        const callback = await legit.approve(authorizationUrl);
        const tokens = await exchangeAuthorization(info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata,
            clientInformation,
            authorizationCode: callback.get('code')!,
            iss: callback.get('iss') ?? undefined,
            codeVerifier,
            redirectUri: REDIRECT_URL
        });
        expect(legit.accessTokens.has(tokens.access_token)).toBe(true);
    });

    it('tokens redeemed with the standalone token helper and saved as returned are refreshed by a later auth() run', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL } as const;
        const provider = new StoredCredentialsProvider(opts);
        expect(await auth(provider as never, { serverUrl: mcp.url })).toBe('REDIRECT');
        const callback = await legit.approve(provider.lastAuthorizationUrl!);
        const info = await discoverOAuthServerInfo(mcp.url);
        provider.saveTokens(
            await fetchToken(provider as never, info.authorizationServerUrl, {
                metadata: info.authorizationServerMetadata,
                authorizationCode: callback.get('code')!,
                iss: callback.get('iss') ?? undefined
            })
        );

        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(tokenGrants(legit)).toEqual(['authorization_code', 'refresh_token']);
        expect(registrations(legit)).toBe(1);
        await connectAndListTools(new StoredCredentialsProvider(opts));
    });

    it('tokens renewed with the standalone refresh helper and saved as returned keep working through the transport', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL } as const;
        const provider = new StoredCredentialsProvider(opts);
        await signIn(provider);
        const info = await discoverOAuthServerInfo(mcp.url);
        provider.saveTokens(
            await refreshAuthorization(info.authorizationServerUrl, {
                metadata: info.authorizationServerMetadata,
                clientInformation: JSON.parse(disk.get('client')!),
                refreshToken: JSON.parse(disk.get('tokens')!).refresh_token
            })
        );

        await connectAndListTools(new StoredCredentialsProvider(opts));
        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(tokenGrants(legit)).toEqual(['authorization_code', 'refresh_token', 'refresh_token']);
        expect(registrations(legit)).toBe(1);
    });

    it('credentials stored without any authorization-server binding (by an earlier version) keep working with an honest server', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL } as const;
        await signIn(new StoredCredentialsProvider(opts));
        for (const key of ['client', 'tokens']) {
            const { issuer: _dropped, ...legacy } = JSON.parse(disk.get(key)!);
            disk.set(key, JSON.stringify(legacy));
        }

        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        expect(tokenGrants(legit)).toEqual(['authorization_code', 'refresh_token']);
        expect(registrations(legit)).toBe(1);
    });

    it('an MCP server that moves to another authorization server: a dynamically registered client signs up there afresh and keeps working', async () => {
        const next = await FakeAuthServer.start('next');
        extraHosts.push(next.host);
        const moving = await FakeMcpServer.start(legit.issuer, t => legit.accessTokens.has(t) || next.accessTokens.has(t));
        extraHosts.push(moving.host);
        const disk: Disk = new Map();
        const opts = { disk } as const;
        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: moving.url })).toBe('AUTHORIZED');
        const oldSecret = JSON.parse(disk.get('client')!).client_secret;

        moving.authorizationServer = next.issuer;
        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: moving.url })).toBe('AUTHORIZED');
        expect(registrations(next)).toBe(1);
        expect(tokenGrants(next)).toContain('client_credentials');
        expect(leakedSecrets(next.requests, [oldSecret])).toEqual([]);

        const client = new Client({ name: 'app', version: '1.0.0' });
        await client.connect(new StreamableHTTPClientTransport(new URL(moving.url), { authProvider: new StoredCredentialsProvider(opts) as never }));
        await client.listTools();
        await client.close();
    });
});
