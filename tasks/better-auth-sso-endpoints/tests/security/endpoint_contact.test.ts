/**
 * Security property: the auth server must never send a request on an SSO
 * provider's behalf to a host the deployment does not permit (not publicly
 * routable and not listed in `trustedOrigins`), whatever provider configuration
 * an SSO manager supplies and however the address is written.
 *
 * Each test configures a provider so that the server would contact an internal
 * address, drives a full SSO sign-in, and asserts only that no connection to
 * that address was attempted. Loopback cases use a real `InternalHost`
 * listener; addresses that cannot be served here (private network, link-local
 * / instance metadata, loopback by name) are observed with a socket-layer
 * `ConnectRecorder`. A fix that refuses at configuration time, at fetch time
 * or before connecting all pass.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
	ConnectRecorder,
	InternalHost,
	LegitIdp,
	makeApp,
	tryRegister,
	tryUpdate,
	type TestApp,
} from "../support/harness";

let idp: LegitIdp;
let internal: InternalHost;
let app: TestApp;

beforeEach(async () => {
	idp = await LegitIdp.start();
	internal = await InternalHost.start();
	// The operator allow-lists only the legitimate IdP origin.
	app = makeApp([idp.issuer]);
});

afterEach(async () => {
	await app.close();
	await internal.close();
	await idp.close();
});

/** Register as `attacker`, drive sign-in, and report how often the internal host was hit. */
async function driveSignIn(providerId: string): Promise<void> {
	const headers = await app.getAuthHeaders("attacker@app.test");
	const signin = await app.auth.handler(
		new Request("http://localhost:3000/api/auth/sign-in/sso", {
			method: "POST",
			headers: {
				...Object.fromEntries(headers),
				"content-type": "application/json",
			},
			body: JSON.stringify({ providerId, callbackURL: "/dashboard" }),
		}),
	);
	const flowHeaders = new Headers(headers);
	const sc =
		(signin.headers as any).getSetCookie?.() ??
		(signin.headers.get("set-cookie") ? [signin.headers.get("set-cookie")!] : []);
	const jar = flowHeaders.get("cookie") ? flowHeaders.get("cookie")!.split("; ") : [];
	for (const c of sc) jar.push(c.split(";")[0]);
	if (jar.length) flowHeaders.set("cookie", jar.join("; "));
	const body: any = await signin.json().catch(() => ({}));
	if (!body?.url) return; // provider not usable: nothing to drive
	await app.simulateOAuthFlow(body.url, flowHeaders);
}

describe("SSO provider endpoints never reach a disallowed host", () => {
	it("skip-discovery registration cannot point the token exchange at an internal host", async () => {
		const headers = await app.getAuthHeaders("attacker@app.test");
		const e = idp.endpoints();
		await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: "attack-token.test",
			providerId: "attack-token",
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				skipDiscovery: true,
				authorizationEndpoint: e.authorizationEndpoint,
				tokenEndpoint: `${internal.origin}/token`,
				jwksEndpoint: e.jwksEndpoint,
				userInfoEndpoint: e.userInfoEndpoint,
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		await driveSignIn("attack-token");
		expect(internal.hits).toBe(0);
	});

	it("skip-discovery registration cannot point the user-info fetch at an internal host", async () => {
		const headers = await app.getAuthHeaders("attacker@app.test");
		const e = idp.endpoints();
		await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: "attack-userinfo.test",
			providerId: "attack-userinfo",
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				skipDiscovery: true,
				authorizationEndpoint: e.authorizationEndpoint,
				tokenEndpoint: e.tokenEndpoint,
				jwksEndpoint: e.jwksEndpoint,
				userInfoEndpoint: `${internal.origin}/userinfo`,
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		await driveSignIn("attack-userinfo");
		expect(internal.hits).toBe(0);
	});

	it("skip-discovery registration cannot point the key (jwks) fetch at an internal host", async () => {
		const headers = await app.getAuthHeaders("attacker@app.test");
		const e = idp.endpoints();
		// No userInfoEndpoint: the server validates the ID token, fetching keys.
		await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: "attack-jwks.test",
			providerId: "attack-jwks",
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				skipDiscovery: true,
				authorizationEndpoint: e.authorizationEndpoint,
				tokenEndpoint: e.tokenEndpoint,
				jwksEndpoint: `${internal.origin}/jwks`,
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		await driveSignIn("attack-jwks");
		expect(internal.hits).toBe(0);
	});

	it("updating an existing provider cannot redirect a fetch to an internal host", async () => {
		const headers = await app.getAuthHeaders("attacker@app.test");
		const e = idp.endpoints();
		// Start from a fully legitimate, allow-listed provider.
		await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: "attack-update.test",
			providerId: "attack-update",
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				skipDiscovery: true,
				authorizationEndpoint: e.authorizationEndpoint,
				tokenEndpoint: e.tokenEndpoint,
				jwksEndpoint: e.jwksEndpoint,
				userInfoEndpoint: e.userInfoEndpoint,
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		// Then move just the token endpoint onto the internal host.
		await tryUpdate(app, headers, {
			providerId: "attack-update",
			oidcConfig: { tokenEndpoint: `${internal.origin}/token` },
		});
		await driveSignIn("attack-update");
		expect(internal.hits).toBe(0);
	});

	/**
	 * Register a skip-discovery provider whose token, user-info and key
	 * endpoints all sit on `base`, then sign in. Only the authorization step
	 * (a browser redirect) uses the allow-listed IdP.
	 */
	async function attackAllEndpoints(providerId: string, base: string) {
		const headers = await app.getAuthHeaders("attacker@app.test");
		const e = idp.endpoints();
		await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: `${providerId}.test`,
			providerId,
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				skipDiscovery: true,
				authorizationEndpoint: e.authorizationEndpoint,
				tokenEndpoint: `${base}/token`,
				jwksEndpoint: `${base}/jwks`,
				userInfoEndpoint: `${base}/userinfo`,
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		await driveSignIn(providerId);
	}

	it("endpoints cannot target a private-network address", async () => {
		const rec = new ConnectRecorder("10.0.0.5", internal);
		rec.install();
		try {
			await attackAllEndpoints("attack-private", "http://10.0.0.5:8080");
		} finally {
			rec.uninstall();
		}
		expect(rec.hits).toBe(0);
	});

	it("endpoints cannot target the cloud instance-metadata address", async () => {
		const rec = new ConnectRecorder("169.254.169.254", internal);
		rec.install();
		try {
			await attackAllEndpoints("attack-metadata", "http://169.254.169.254/latest/meta-data");
		} finally {
			rec.uninstall();
		}
		expect(rec.hits).toBe(0);
	});

	it("endpoints cannot target loopback written in short form", async () => {
		// "127.1" is the same loopback address as 127.0.0.1, written short.
		const port = new URL(internal.origin).port;
		await attackAllEndpoints("attack-short", `http://127.1:${port}`);
		expect(internal.hits).toBe(0);
	});

	it("endpoints cannot target loopback by name", async () => {
		const rec = new ConnectRecorder("localhost", internal);
		rec.install();
		try {
			await attackAllEndpoints("attack-name", "http://localhost:8080");
		} finally {
			rec.uninstall();
		}
		expect(rec.hits).toBe(0);
	});

	it("endpoints cannot target another private-network range", async () => {
		const rec = new ConnectRecorder("192.168.1.20", internal);
		rec.install();
		try {
			await attackAllEndpoints("attack-private-192", "http://192.168.1.20:8080");
		} finally {
			rec.uninstall();
		}
		expect(rec.hits).toBe(0);
	});

	it("endpoints cannot target the unspecified address", async () => {
		// 0.0.0.0 reaches services listening on the server's own machine.
		const port = new URL(internal.origin).port;
		await attackAllEndpoints("attack-unspecified", `http://0.0.0.0:${port}`);
		expect(internal.hits).toBe(0);
	});

	it("an explicit endpoint override cannot smuggle an internal host past discovery", async () => {
		const headers = await app.getAuthHeaders("attacker@app.test");
		const e = idp.endpoints();
		// skipDiscovery is NOT set: the server runs discovery against the
		// allow-listed issuer, but the caller also supplies an explicit
		// tokenEndpoint pointing at the internal host.
		await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: "attack-override.test",
			providerId: "attack-override",
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				discoveryEndpoint: e.discoveryEndpoint,
				tokenEndpoint: `${internal.origin}/token`,
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		await driveSignIn("attack-override");
		expect(internal.hits).toBe(0);
	});
});
