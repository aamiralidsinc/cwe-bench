import { describe, expect, it } from "vitest";

import { FetchRequestAdapter, KiotaClientFactory } from "@product/fetch";

import { authProvider, COOKIE, hasHeader, ok, PROXY, recorder, redirect, requestInformation } from "../support/helpers";

/**
 * The caller may attach a proxy credential to the request itself. It is a credential for the
 * addressed origin exactly like the bearer token and the cookie, so a redirect to another origin
 * must not carry it.
 */
async function send(location: string, extra: Record<string, string>) {
	const rec = recorder([redirect(location, 302), ok()]);
	const httpClient = KiotaClientFactory.create(rec.fetchFn);
	const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
	await adapter.sendNoResponseContent(requestInformation("https://api.example.com/v1/me", extra), undefined);
	return rec;
}

describe("proxy credential is not carried to another origin", () => {
	it("cross-host redirect removes the proxy credential", async () => {
		const rec = await send("https://collector.example/ingest", { "Proxy-Authorization": PROXY });
		expect(rec.calls).toHaveLength(2);
		expect(hasHeader(rec.calls[0].headers, "proxy-authorization")).toBe(true);
		expect(hasHeader(rec.calls[1].headers, "proxy-authorization")).toBe(false);
	});

	it("scheme change removes the proxy credential", async () => {
		const rec = await send("http://api.example.com/collect", { "Proxy-Authorization": PROXY });
		expect(hasHeader(rec.calls[1].headers, "proxy-authorization")).toBe(false);
	});

	it("a lower-case and an upper-case spelling are both removed", async () => {
		const rec = await send("https://collector.example/ingest", { "proxy-authorization": PROXY, "PROXY-AUTHORIZATION": "Basic OTHER" });
		expect(hasHeader(rec.calls[1].headers, "proxy-authorization")).toBe(false);
	});

	it("the proxy credential is removed whether or not other headers are present", async () => {
		const rec = await send("https://collector.example/ingest", { "Proxy-Authorization": PROXY, Cookie: COOKIE });
		expect(hasHeader(rec.calls[1].headers, "proxy-authorization")).toBe(false);
	});
});
