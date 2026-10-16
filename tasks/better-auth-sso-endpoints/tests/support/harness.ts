/**
 * Behavioural harness for the SSO provider-endpoint tests.
 *
 * Two kinds of local HTTP listeners run on the loopback interface:
 *
 *   - A legitimate identity provider (`oauth2-mock-server`) whose origin the
 *     application operator has explicitly allow-listed via `trustedOrigins`.
 *     It serves discovery, authorization, token, jwks and userinfo so a full
 *     OIDC sign-in can complete against it.
 *
 *   - One or more `InternalHost` listeners that stand in for infrastructure the
 *     auth server can reach on its own network but that no provider was ever
 *     permitted to use (databases, metadata services, admin panels). Every
 *     request they receive is recorded, so a test can assert on whether the
 *     server was coerced into contacting them, never on error text or status.
 *
 * Nothing here contacts a real external host.
 */
import http from "node:http";
import net from "node:net";
import type { AddressInfo } from "node:net";

import { betterAuth } from "better-auth";
import { memoryAdapter } from "better-auth/adapters/memory";
import { createAuthClient } from "better-auth/client";
import { organization } from "better-auth/plugins";
import { OAuth2Server } from "oauth2-mock-server";

import { sso } from "@better-auth/sso";
import { ssoClient } from "@better-auth/sso/client";

export interface RecordedRequest {
	method: string;
	path: string;
}

/** A loopback listener that records every request and never redirects anywhere useful. */
export class InternalHost {
	readonly requests: RecordedRequest[] = [];
	private readonly sockets = new Set<import("node:net").Socket>();
	readonly origin: string;

	private constructor(private readonly server: http.Server) {
		const { port } = server.address() as AddressInfo;
		this.origin = `http://127.0.0.1:${port}`;
		server.on("connection", (s) => {
			this.sockets.add(s);
			s.on("close", () => this.sockets.delete(s));
		});
	}

	static async start(): Promise<InternalHost> {
		const server = http.createServer();
		const host = await new Promise<InternalHost>((resolve) => {
			server.listen(0, "127.0.0.1", () => resolve(new InternalHost(server)));
		});
		server.on("request", (req, res) => {
			host.requests.push({ method: req.method ?? "GET", path: req.url ?? "/" });
			// Answer like a reachable-but-useless internal service: 200 with a small
			// JSON body. The point is only that we were contacted at all.
			res.writeHead(200, { "content-type": "application/json" });
			res.end(
				JSON.stringify({ internal: true, keys: [], email: "x@evil.test" }),
			);
		});
		return host;
	}

	/** Number of times the auth server reached this host. */
	get hits(): number {
		return this.requests.length;
	}

	async close(): Promise<void> {
		for (const s of this.sockets) s.destroy();
		await new Promise<void>((resolve) => this.server.close(() => resolve()));
	}
}

/**
 * Records every outbound TCP connection attempt the process makes to one host,
 * at the socket layer (`net.Socket.prototype.connect`, which plain and TLS
 * sockets both go through), and reroutes it to a local `InternalHost` so the
 * caller gets an ordinary HTTP answer without touching the network. Used for
 * internal addresses that cannot be served in the test environment (a
 * private-network or link-local / instance-metadata address) and for loopback
 * names. Connections to any other host are untouched.
 *
 * Counting connection attempts (rather than calls to `fetch`) means a fix that
 * refuses before any connection is made passes, wherever it sits.
 */
export class ConnectRecorder {
	readonly attempts: string[] = [];
	private original: typeof net.Socket.prototype.connect | undefined;

	constructor(
		private readonly hostname: string,
		private readonly sink: InternalHost,
	) {}

	install(): void {
		const original = net.Socket.prototype.connect;
		this.original = original;
		const target = this.hostname;
		const attempts = this.attempts;
		const sinkPort = Number(new URL(this.sink.origin).port);
		net.Socket.prototype.connect = function (this: net.Socket, ...args: any[]) {
			// net.connect() passes an internal [options, cb] array; direct calls
			// pass (options[, cb]) or (port[, host][, cb]).
			const first = args[0];
			const opts =
				Array.isArray(first) && first[0] && typeof first[0] === "object"
					? first[0]
					: first && typeof first === "object"
						? first
						: undefined;
			if (opts) {
				const host = String(opts.host ?? "").replace(/^\[|\]$/g, "");
				if (host === target) {
					attempts.push(`${host}:${opts.port}`);
					opts.host = "127.0.0.1";
					opts.port = sinkPort;
				}
			} else if (typeof first === "number" || typeof first === "string") {
				const host = typeof args[1] === "string" ? args[1] : "";
				if (host === target) {
					attempts.push(`${host}:${first}`);
					args[0] = sinkPort;
					args[1] = "127.0.0.1";
				}
			}
			return (original as any).apply(this, args);
		} as typeof net.Socket.prototype.connect;
	}

	uninstall(): void {
		if (this.original) net.Socket.prototype.connect = this.original;
	}

	get hits(): number {
		return this.attempts.length;
	}
}

/**
 * A legitimate OIDC identity provider on loopback. Its discovery document,
 * token signing, jwks and userinfo all work so a real sign-in can complete.
 */
export class LegitIdp {
	private constructor(
		private readonly server: OAuth2Server,
		readonly issuer: string,
	) {}

	static async start(email = "legit-user@idp.test"): Promise<LegitIdp> {
		const server = new OAuth2Server();
		await server.issuer.keys.generate("RS256");
		server.service.on("beforeUserinfo", (userInfoResponse) => {
			userInfoResponse.body = {
				sub: "legit-subject",
				email,
				email_verified: true,
				name: "Legit User",
				picture: "https://idp.test/pic.png",
			};
			userInfoResponse.statusCode = 200;
		});
		server.service.on("beforeTokenSigning", (token) => {
			token.payload.email = email;
			token.payload.email_verified = true;
			token.payload.name = "Legit User";
		});
		// Bind to an ephemeral port on the IPv4 loopback interface. Using the
		// literal 127.0.0.1 (rather than "localhost") keeps the issuer URL and
		// every server-side fetch on IPv4, avoiding IPv4/IPv6 resolution
		// mismatches between environments.
		await server.start(0, "127.0.0.1");
		// oauth2-mock-server names a loopback issuer "localhost"; pin it to the
		// IPv4 literal it actually listens on.
		server.issuer.url = `http://127.0.0.1:${server.address().port}`;
		const issuer = server.issuer.url;
		return new LegitIdp(server, issuer);
	}

	endpoints() {
		return {
			authorizationEndpoint: `${this.issuer}/authorize`,
			tokenEndpoint: `${this.issuer}/token`,
			jwksEndpoint: `${this.issuer}/jwks`,
			userInfoEndpoint: `${this.issuer}/userinfo`,
			discoveryEndpoint: `${this.issuer}/.well-known/openid-configuration`,
		};
	}

	async close(): Promise<void> {
		await this.server.stop().catch(() => {});
	}
}

export interface TestApp {
	auth: ReturnType<typeof betterAuth>;
	authClient: ReturnType<typeof createAuthClient>;
	getAuthHeaders: (email?: string) => Promise<Headers>;
	simulateOAuthFlow: (
		authUrl: string,
		headers: Headers,
	) => Promise<{ callbackURL: string; headers: Headers }>;
	close: () => Promise<void>;
}

/**
 * Build an application that uses the SSO plugin, backed by an in-memory store,
 * with `trustedOrigins` naming the legitimate IdP origins the operator approved.
 */
export function makeApp(trustedOrigins: string[] = []): TestApp {
	const data = {
		user: [] as any[],
		session: [] as any[],
		verification: [] as any[],
		account: [] as any[],
		ssoProvider: [] as any[],
		member: [] as any[],
		organization: [] as any[],
	};
	const auth = betterAuth({
		database: memoryAdapter(data),
		baseURL: "http://localhost:3000",
		secret: "test-secret-that-is-sufficiently-long-for-validation-xx",
		trustedOrigins,
		emailAndPassword: { enabled: true },
		plugins: [sso(), organization()],
	});

	const customFetchImpl = async (url: string | URL | Request, init?: any) =>
		auth.handler(new Request(url, init));

	const authClient = createAuthClient({
		baseURL: "http://localhost:3000",
		plugins: [ssoClient()],
		fetchOptions: { customFetchImpl },
	});

	function parseSetCookie(from: Response, into: Headers) {
		const sc =
			(from.headers as any).getSetCookie?.() ??
			(from.headers.get("set-cookie") ? [from.headers.get("set-cookie")!] : []);
		const existing = into.get("cookie");
		const jar = existing ? existing.split("; ") : [];
		for (const c of sc) jar.push(c.split(";")[0]);
		if (jar.length) into.set("cookie", jar.join("; "));
	}

	async function getAuthHeaders(email = "app-user@app.test"): Promise<Headers> {
		const headers = new Headers();
		await authClient.signUp.email({
			email,
			password: "password1234",
			name: "App User",
		});
		const res = await auth.handler(
			new Request("http://localhost:3000/api/auth/sign-in/email", {
				method: "POST",
				headers: { "content-type": "application/json" },
				body: JSON.stringify({ email, password: "password1234" }),
			}),
		);
		parseSetCookie(res, headers);
		return headers;
	}

	async function simulateOAuthFlow(authUrl: string, headers: Headers) {
		// 1) The browser visits the IdP authorize URL and is redirected back
		//    to our callback with ?code=...&state=...
		const authResp = await fetch(authUrl, { method: "GET", redirect: "manual" });
		const location = authResp.headers.get("location");
		if (!location) throw new Error("IdP did not redirect to a callback");

		// 2) The browser hits our callback. This is where the server performs
		//    its server-side token / userinfo / jwks fetches.
		const newHeaders = new Headers(headers);
		const cbResp = await auth.handler(
			new Request(location, { method: "GET", headers }),
		);
		parseSetCookie(cbResp, newHeaders);
		const callbackURL = cbResp.headers.get("location") || "";
		return { callbackURL, headers: newHeaders };
	}

	return {
		auth,
		authClient,
		getAuthHeaders,
		simulateOAuthFlow,
		close: async () => {},
	};
}

/** Attempt a provider registration; never throws (a rejected registration is a valid outcome). */
export async function tryRegister(
	app: TestApp,
	headers: Headers,
	body: Record<string, unknown>,
): Promise<{ ok: boolean; error?: unknown }> {
	try {
		await app.auth.api.registerSSOProvider({ body: body as any, headers });
		return { ok: true };
	} catch (error) {
		return { ok: false, error };
	}
}

/** Attempt a provider update; never throws. */
export async function tryUpdate(
	app: TestApp,
	headers: Headers,
	body: Record<string, unknown>,
): Promise<{ ok: boolean; error?: unknown }> {
	try {
		await app.auth.api.updateSSOProvider({ body: body as any, headers });
		return { ok: true };
	} catch (error) {
		return { ok: false, error };
	}
}
