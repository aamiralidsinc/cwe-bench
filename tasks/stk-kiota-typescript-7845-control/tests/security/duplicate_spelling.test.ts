import { describe, expect, it } from "vitest";

import { FetchRequestAdapter, KiotaClientFactory } from "@product/fetch";

import { authProvider, credentialKeys, hasHeader, ok, recorder, redirect, requestInformation } from "../support/helpers";

/**
 * A supported configuration puts an authentication middleware in front of the chain. That
 * middleware writes the bearer token under its own spelling of the header name, next to the
 * request the adapter already authenticated. Both spellings are the caller's credential and both
 * must leave a request that changes origin.
 */
async function sendWithAuthenticationMiddleware(location: string, extra: Record<string, string> = {}) {
	const original = authProvider();
	const rec = recorder([redirect(location, 302), ok()]);
	const httpClient = KiotaClientFactory.create(rec.fetchFn, undefined, original);
	const adapter = new FetchRequestAdapter(original, undefined, undefined, httpClient);
	await adapter.sendNoResponseContent(requestInformation("https://api.example.com/v1/me", extra), undefined);
	return rec;
}

describe("the credential is removed under every spelling on the request", () => {
	it("cross-host redirect removes both the adapter spelling and the authentication middleware spelling", async () => {
		const rec = await sendWithAuthenticationMiddleware("https://collector.example/ingest");
		expect(rec.calls).toHaveLength(2);
		// The first request carries the token, so the follow-up assertion is meaningful.
		expect(hasHeader(rec.calls[0].headers, "authorization")).toBe(true);
		expect(credentialKeys(rec.calls[1].headers)).toEqual([]);
	});

	it("scheme change removes both spellings", async () => {
		const rec = await sendWithAuthenticationMiddleware("http://api.example.com/collect");
		expect(credentialKeys(rec.calls[1].headers)).toEqual([]);
	});

	it("a caller-supplied canonical spelling is removed too", async () => {
		const rec = await sendWithAuthenticationMiddleware("https://collector.example/ingest", { Authorization: "Bearer CALLER" });
		expect(hasHeader(rec.calls[0].headers, "authorization")).toBe(true);
		expect(credentialKeys(rec.calls[1].headers)).toEqual([]);
	});

	it("a caller-supplied upper-case spelling is removed too", async () => {
		const rec = await sendWithAuthenticationMiddleware("https://collector.example/ingest", { AUTHORIZATION: "Bearer CALLER" });
		expect(credentialKeys(rec.calls[1].headers)).toEqual([]);
	});
});
