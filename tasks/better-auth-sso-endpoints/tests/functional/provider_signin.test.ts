/**
 * Functional tests: legitimate provider registration, update and sign-in must
 * keep working exactly as before. These guard against a fix that "closes" the
 * flaw by over-restricting the feature (e.g. refusing every endpoint, or
 * refusing allow-listed internal IdPs, or breaking the sign-in flow).
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
	LegitIdp,
	makeApp,
	tryRegister,
	tryUpdate,
	type TestApp,
} from "../support/harness";

let idp: LegitIdp;
let app: TestApp;

beforeEach(async () => {
	idp = await LegitIdp.start();
	// The operator allow-lists the (loopback) IdP they intentionally run.
	app = makeApp([idp.issuer]);
});

afterEach(async () => {
	await app.close();
	await idp.close();
});

async function registerLegit(providerId: string, opts: Record<string, unknown>) {
	const headers = await app.getAuthHeaders(`${providerId}@app.test`);
	const e = idp.endpoints();
	const r = await tryRegister(app, headers, {
		issuer: idp.issuer,
		domain: `${providerId}.test`,
		providerId,
		oidcConfig: {
			clientId: "c",
			clientSecret: "s",
			mapping: { id: "sub", email: "email", name: "name" },
			...opts,
		},
	});
	return { headers, e, r };
}

/** Drive a full sign-in for `providerId` and return the final callback redirect. */
async function signIn(providerId: string): Promise<string> {
	const headers = await app.getAuthHeaders(`signin-${providerId}@app.test`);
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
	expect(body?.url, "sign-in should return an authorization URL").toBeTruthy();
	const { callbackURL } = await app.simulateOAuthFlow(body.url, flowHeaders);
	return callbackURL;
}

describe("legitimate SSO still works", () => {
	it("registers a skip-discovery provider on an allow-listed IdP and signs in", async () => {
		const e = idp.endpoints();
		const { r } = await registerLegit("legit-skip", {
			skipDiscovery: true,
			authorizationEndpoint: e.authorizationEndpoint,
			tokenEndpoint: e.tokenEndpoint,
			jwksEndpoint: e.jwksEndpoint,
			userInfoEndpoint: e.userInfoEndpoint,
		});
		expect(r.ok).toBe(true);
		const callbackURL = await signIn("legit-skip");
		expect(callbackURL).toContain("/dashboard");
	});

	it("registers a discovery-based provider on an allow-listed IdP and signs in", async () => {
		const e = idp.endpoints();
		const { r } = await registerLegit("legit-discovery", {
			discoveryEndpoint: e.discoveryEndpoint,
		});
		expect(r.ok).toBe(true);
		const callbackURL = await signIn("legit-discovery");
		expect(callbackURL).toContain("/dashboard");
	});

	it("updates a provider endpoint to another allow-listed value and still signs in", async () => {
		const e = idp.endpoints();
		const { headers, r } = await registerLegit("legit-update", {
			skipDiscovery: true,
			authorizationEndpoint: e.authorizationEndpoint,
			tokenEndpoint: e.tokenEndpoint,
			jwksEndpoint: e.jwksEndpoint,
			userInfoEndpoint: e.userInfoEndpoint,
		});
		expect(r.ok).toBe(true);
		// Re-point the user-info endpoint to another path on the same allow-listed IdP.
		const u = await tryUpdate(app, headers, {
			providerId: "legit-update",
			oidcConfig: { userInfoEndpoint: e.userInfoEndpoint },
		});
		expect(u.ok).toBe(true);
		const callbackURL = await signIn("legit-update");
		expect(callbackURL).toContain("/dashboard");
	});

	it("accepts a provider whose endpoints are on a publicly routable host", async () => {
		const headers = await app.getAuthHeaders("public-host@app.test");
		const r = await tryRegister(app, headers, {
			issuer: "https://8.8.8.8",
			domain: "public-host.test",
			providerId: "public-host",
			oidcConfig: {
				clientId: "c",
				clientSecret: "s",
				skipDiscovery: true,
				authorizationEndpoint: "https://8.8.8.8/authorize",
				tokenEndpoint: "https://8.8.8.8/token",
				jwksEndpoint: "https://8.8.8.8/jwks",
				userInfoEndpoint: "https://8.8.8.8/userinfo",
				mapping: { id: "sub", email: "email", name: "name" },
			},
		});
		expect(r.ok).toBe(true);
	});

	it("accepts an internal IdP whose origin the operator added to the allow-list", async () => {
		// The escape hatch: a loopback origin that IS in trustedOrigins must be
		// accepted even though it is not publicly routable.
		const e = idp.endpoints();
		const headers = await app.getAuthHeaders("trusted-internal@app.test");
		const r = await tryRegister(app, headers, {
			issuer: idp.issuer,
			domain: "trusted-internal.test",
			providerId: "trusted-internal",
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
		expect(r.ok).toBe(true);
	});
});
