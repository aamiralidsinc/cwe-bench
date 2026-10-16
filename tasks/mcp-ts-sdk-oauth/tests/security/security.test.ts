/**
 * Security tests: an MCP server (malicious, or compromised after the client signed in)
 * names an authorization server of the attacker's choosing. Whatever the client does,
 * the credentials it holds for its legitimate authorization server (configured client
 * secrets / signing keys / static assertions, and client secrets / refresh tokens saved
 * from an earlier sign-in) must never reach the attacker's authorization server.
 *
 * Every test asserts only on what the attacker's server received.
 *
 * Ported from Hadi's task (2026-10-15); the last two groups were added for the cwe-bench
 * version (2026-10-16).
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
    StaticPrivateKeyJwtProvider,
    StreamableHTTPClientTransport,
    withOAuth
} from '@modelcontextprotocol/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import type { Disk } from '../support/harness';
import {
    clientAssertionsPresented,
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
let attacker: FakeAuthServer;
let mcp: FakeMcpServer;
let extraHosts: Host[];
let restoreConsole: () => void;

beforeEach(async () => {
    restoreConsole = silenceConsole();
    extraHosts = [];
    legit = await FakeAuthServer.start('legit');
    attacker = await FakeAuthServer.start('attacker');
    mcp = await FakeMcpServer.start(legit.issuer, t => legit.accessTokens.has(t));
});

afterEach(async () => {
    restoreConsole();
    await Promise.all([legit.host.close(), attacker.host.close(), mcp.host.close(), ...extraHosts.map(h => h.close())]);
});

/** The application's own discovery against the MCP server, as it would do before requesting a token. */
async function discoverAttackerViaMcp(expectedAs: FakeAuthServer = attacker) {
    const info = await discoverOAuthServerInfo(mcp.url);
    // Sanity: the attack is in place — discovery resolved the attacker-chosen authorization server.
    expect(info.authorizationServerMetadata?.issuer ?? info.authorizationServerUrl).toBe(expectedAs.issuer);
    return info;
}

function attackerSawDiscovery(as: FakeAuthServer = attacker): boolean {
    return as.requests.some(r => r.path.startsWith('/.well-known/'));
}

async function connectOnce(provider: unknown): Promise<void> {
    const client = new Client({ name: 'victim-app', version: '1.0.0' });
    const transport = new StreamableHTTPClientTransport(new URL(mcp.url), { authProvider: provider as never });
    await settle(client.connect(transport));
    await settle(client.close());
}

/** Earlier, legitimate interactive sign-in through the transport (user approves at the legitimate AS). */
async function interactiveSignIn(provider: StoredCredentialsProvider): Promise<void> {
    const client = new Client({ name: 'victim-app', version: '1.0.0' });
    const transport = new StreamableHTTPClientTransport(new URL(mcp.url), { authProvider: provider as never });
    const first = await settle(client.connect(transport));
    expect(first.ok).toBe(false);
    expect(provider.lastAuthorizationUrl?.href.startsWith(legit.issuer)).toBe(true);
    const callback = await legit.approve(provider.lastAuthorizationUrl!);
    await transport.finishAuth(callback);
    await settle(client.close());
    const client2 = new Client({ name: 'victim-app', version: '1.0.0' });
    await client2.connect(new StreamableHTTPClientTransport(new URL(mcp.url), { authProvider: provider as never }));
    await client2.listTools();
    await client2.close();
}

/** Earlier, legitimate interactive sign-in driven through auth() directly. */
async function interactiveSignInViaAuth(provider: StoredCredentialsProvider): Promise<void> {
    expect(await auth(provider as never, { serverUrl: mcp.url })).toBe('REDIRECT');
    const callback = await legit.approve(provider.lastAuthorizationUrl!);
    expect(
        await auth(provider as never, { serverUrl: mcp.url, authorizationCode: callback.get('code')!, iss: callback.get('iss') ?? undefined })
    ).toBe('AUTHORIZED');
}

function storedSecrets(disk: Disk): { clientSecret?: string; refreshToken?: string } {
    const client = disk.has('client') ? JSON.parse(disk.get('client')!) : {};
    const tokens = disk.has('tokens') ? JSON.parse(disk.get('tokens')!) : {};
    return { clientSecret: client.client_secret, refreshToken: tokens.refresh_token };
}

describe('token requests made with the standalone token helper', () => {
    it('client_credentials: a bundled provider pinned to its authorization server does not send its client secret to the server named by the MCP server', async () => {
        const secret = `cc-secret-${rnd()}`;
        legit.preRegister({ client_id: 'reporting-job', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'reporting-job', clientSecret: secret, expectedIssuer: legit.issuer });

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(
            fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata, resource: new URL(mcp.url) })
        );

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [secret])).toEqual([]);
    });

    it('private_key_jwt: a signing provider pinned to its authorization server presents no client assertion to the server named by the MCP server', async () => {
        const key = `hs256-key-${rnd()}-${rnd()}-${rnd()}`;
        legit.preRegister({ client_id: 'signer', hsKey: key });
        const provider = new PrivateKeyJwtProvider({ clientId: 'signer', privateKey: key, algorithm: 'HS256', expectedIssuer: legit.issuer });

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(clientAssertionsPresented(attacker.requests)).toEqual([]);
    });

    it('static private_key_jwt: a pre-built client assertion is not presented to the server named by the MCP server', async () => {
        const assertion = `eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzdGF0aWMifQ.${rnd()}`;
        legit.preRegister({ client_id: 'static-client', staticAssertion: assertion });
        const provider = new StaticPrivateKeyJwtProvider({ clientId: 'static-client', jwtBearerAssertion: assertion, expectedIssuer: legit.issuer });

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [assertion])).toEqual([]);
        expect(clientAssertionsPresented(attacker.requests)).toEqual([]);
    });

    it('cross-app access (jwt-bearer): the client secret is not sent to the server named by the MCP server', async () => {
        const secret = `xaa-secret-${rnd()}`;
        legit.preRegister({ client_id: 'xaa-client', client_secret: secret });
        const provider = new CrossAppAccessProvider({
            assertion: async () => `idp-grant-${rnd()}`,
            clientId: 'xaa-client',
            clientSecret: secret,
            expectedIssuer: legit.issuer
        });

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        provider.saveAuthorizationServerUrl(info.authorizationServerMetadata?.issuer ?? info.authorizationServerUrl);
        provider.saveResourceUrl?.(mcp.url);
        await settle(fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [secret])).toEqual([]);
    });

    it('a client registered at the legitimate server in an earlier sign-in does not send that registration secret elsewhere', async () => {
        const disk: Disk = new Map();
        expect(await auth(new StoredCredentialsProvider({ disk }) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        const { clientSecret } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(
            fetchToken(new StoredCredentialsProvider({ disk }) as never, info.authorizationServerUrl, {
                metadata: info.authorizationServerMetadata
            })
        );

        expect(leakedSecrets(attacker.requests, [clientSecret])).toEqual([]);
    });

    it('without authorization-server metadata (URL only) the configured secret is still not sent to the named server', async () => {
        const secret = `cc-secret-${rnd()}`;
        legit.preRegister({ client_id: 'job', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'job', clientSecret: secret, expectedIssuer: legit.issuer });

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(fetchToken(provider, info.authorizationServerUrl));

        expect(leakedSecrets(attacker.requests, [secret])).toEqual([]);
    });

    it('credentials the provider only loads while preparing the token request are not sent to the named server', async () => {
        const secret = `vault-secret-${rnd()}`;
        legit.preRegister({ client_id: 'vaulted', client_secret: secret });
        let loaded: Record<string, string> | undefined;
        const provider = {
            get redirectUrl() {
                return undefined;
            },
            get clientMetadata() {
                return { client_name: 'vaulted', redirect_uris: [], grant_types: ['client_credentials'] };
            },
            // Credentials are fetched lazily from a secret store on the first token request.
            clientInformation: () => loaded,
            tokens: () => undefined,
            saveTokens: () => {},
            redirectToAuthorization: () => {},
            saveCodeVerifier: () => {},
            codeVerifier: () => 'unused',
            prepareTokenRequest: () => {
                loaded = { client_id: 'vaulted', client_secret: secret, issuer: legit.issuer };
                return new URLSearchParams({ grant_type: 'client_credentials' });
            }
        };

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(fetchToken(provider as never, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata }));

        expect(leakedSecrets(attacker.requests, [secret])).toEqual([]);
    });

    it('a different tenant on the same identity provider host does not receive the secret pinned to another tenant', async () => {
        const idp = await Host.start();
        extraHosts.push(idp);
        const acme = new FakeAuthServer(idp, 'acme', '/realms/acme');
        const lookalike = new FakeAuthServer(idp, 'acme-support', '/realms/acme-support');
        const secret = `tenant-secret-${rnd()}`;
        acme.preRegister({ client_id: 'svc', client_secret: secret });
        const provider = new ClientCredentialsProvider({ clientId: 'svc', clientSecret: secret, expectedIssuer: acme.issuer });

        mcp.turnMalicious(lookalike.issuer);
        const info = await discoverAttackerViaMcp(lookalike);
        await settle(fetchToken(provider, info.authorizationServerUrl, { metadata: info.authorizationServerMetadata }));

        expect(attackerSawDiscovery(lookalike)).toBe(true);
        expect(leakedSecrets(lookalike.requests, [secret])).toEqual([]);
    });

    it('authorization_code redemption: the stored client secret is not sent to the server named by the MCP server', async () => {
        const disk: Disk = new Map();
        const provider = new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL });
        await interactiveSignInViaAuth(provider);
        const { clientSecret } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        provider.saveCodeVerifier(`v-${rnd()}${rnd()}${rnd()}`);
        await settle(
            fetchToken(provider as never, info.authorizationServerUrl, {
                metadata: info.authorizationServerMetadata,
                authorizationCode: `code-${rnd()}`,
                iss: attacker.issuer
            })
        );

        expect(leakedSecrets(attacker.requests, [clientSecret])).toEqual([]);
    });
});

describe('credentials persisted by the application and validated on load with the SDK schemas', () => {
    it('transport: after an earlier sign-in, a compromised MCP server does not obtain the stored refresh token or client secret', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL, clientInfo: 'schema', tokens: 'schema' } as const;
        await interactiveSignIn(new StoredCredentialsProvider(opts));
        const { clientSecret, refreshToken } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();
        expect(refreshToken).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        await connectOnce(new StoredCredentialsProvider(opts));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret, refreshToken])).toEqual([]);
    });

    it('auth(): a refresh token loaded through the token schema is not sent to the authorization server named by the MCP server', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL, clientInfo: 'verbatim', tokens: 'schema' } as const;
        await interactiveSignInViaAuth(new StoredCredentialsProvider(opts));
        const { refreshToken } = storedSecrets(disk);
        expect(refreshToken).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        await settle(auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [refreshToken])).toEqual([]);
    });

    it('auth(): a registered machine client loaded through the client-information schema does not send its secret to the named server', async () => {
        const disk: Disk = new Map();
        const opts = { disk, clientInfo: 'schema', tokens: 'verbatim' } as const;
        expect(await auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url })).toBe('AUTHORIZED');
        const { clientSecret } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        await settle(auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret])).toEqual([]);
    });

    it('transport: pre-registered credentials (saved with their issuer) loaded through the client-information schema are not sent to the named server', async () => {
        const secret = `prereg-secret-${rnd()}`;
        legit.preRegister({ client_id: 'svc-account', client_secret: secret });
        const disk: Disk = new Map([['client', JSON.stringify({ client_id: 'svc-account', client_secret: secret, issuer: legit.issuer })]]);
        const opts = { disk, clientInfo: 'schema', readOnlyClientInfo: true } as const;

        mcp.turnMalicious(attacker.issuer);
        await connectOnce(new StoredCredentialsProvider(opts));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [secret])).toEqual([]);
    });

    it('withOAuth() middleware: a registered client loaded through the full client-information schema does not send its secret to the named server', async () => {
        const disk: Disk = new Map();
        const opts = { disk, clientInfo: 'full-schema' } as const;
        const rpc = { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream' } };
        const body = JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} });

        const first = await withOAuth(new StoredCredentialsProvider(opts) as never, mcp.url)(fetch)(mcp.url, { ...rpc, body });
        expect(first.status).toBe(200);
        const { clientSecret } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        await settle(withOAuth(new StoredCredentialsProvider(opts) as never, mcp.url)(fetch)(mcp.url, { ...rpc, body }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret])).toEqual([]);
    });
});

describe('saved credentials handed to the other standalone token helpers', () => {
    it('refresh helper: a refresh token and client secret saved from an earlier sign-in are not sent to the server named by the MCP server', async () => {
        const disk: Disk = new Map();
        await interactiveSignInViaAuth(new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL }));
        const { clientSecret, refreshToken } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();
        expect(refreshToken).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        await settle(
            refreshAuthorization(info.authorizationServerUrl, {
                metadata: info.authorizationServerMetadata,
                clientInformation: JSON.parse(disk.get('client')!),
                refreshToken: refreshToken!
            })
        );

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret, refreshToken])).toEqual([]);
    });

    it('code-exchange helper: a client secret saved from an earlier sign-in is not sent to the server named by the MCP server', async () => {
        const disk: Disk = new Map();
        await interactiveSignInViaAuth(new StoredCredentialsProvider({ disk, redirectUrl: REDIRECT_URL }));
        const { clientSecret } = storedSecrets(disk);
        expect(clientSecret).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        const info = await discoverAttackerViaMcp();
        // The application's own authorization-code flow, now at the server the MCP server names.
        await settle(
            exchangeAuthorization(info.authorizationServerUrl, {
                metadata: info.authorizationServerMetadata,
                clientInformation: JSON.parse(disk.get('client')!),
                authorizationCode: `code-${rnd()}`,
                iss: attacker.issuer,
                codeVerifier: `v-${rnd()}${rnd()}${rnd()}`,
                redirectUri: REDIRECT_URL
            })
        );

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret])).toEqual([]);
    });
});

describe('tokens the application obtained with the standalone helpers and saved as returned', () => {
    it('auth(): tokens redeemed with the standalone token helper in an earlier sign-in are not refreshed at the server named by a compromised MCP server', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL } as const;
        const provider = new StoredCredentialsProvider(opts);
        expect(await auth(provider as never, { serverUrl: mcp.url })).toBe('REDIRECT');
        const callback = await legit.approve(provider.lastAuthorizationUrl!);
        const info = await discoverOAuthServerInfo(mcp.url);
        const tokens = await fetchToken(provider as never, info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata,
            authorizationCode: callback.get('code')!,
            iss: callback.get('iss') ?? undefined
        });
        provider.saveTokens(tokens);
        const { clientSecret, refreshToken } = storedSecrets(disk);
        expect(refreshToken).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        await settle(auth(new StoredCredentialsProvider(opts) as never, { serverUrl: mcp.url }));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret, refreshToken])).toEqual([]);
    });

    it('transport: tokens renewed with the standalone refresh helper are not refreshed at the server named by a compromised MCP server', async () => {
        const disk: Disk = new Map();
        const opts = { disk, redirectUrl: REDIRECT_URL } as const;
        const provider = new StoredCredentialsProvider(opts);
        await interactiveSignInViaAuth(provider);
        const info = await discoverOAuthServerInfo(mcp.url);
        const saved = JSON.parse(disk.get('tokens')!);
        const renewed = await refreshAuthorization(info.authorizationServerUrl, {
            metadata: info.authorizationServerMetadata,
            clientInformation: JSON.parse(disk.get('client')!),
            refreshToken: saved.refresh_token
        });
        provider.saveTokens(renewed);
        const { clientSecret, refreshToken } = storedSecrets(disk);
        expect(refreshToken).toBeTruthy();

        mcp.turnMalicious(attacker.issuer);
        await connectOnce(new StoredCredentialsProvider(opts));

        expect(attackerSawDiscovery()).toBe(true);
        expect(leakedSecrets(attacker.requests, [clientSecret, refreshToken])).toEqual([]);
    });
});
