import { describe, expect, it } from "vitest";

import { FetchRequestAdapter, KiotaClientFactory } from "@product/fetch";

import { authProvider, COOKIE, hasHeader, ok, recorder, redirect, requestInformation, TRACE } from "../support/helpers";

/**
 * The default request path: a request is authenticated, the chain sees a redirect response, and
 * the chain sends the follow-up request itself. The recorder is the transport at the end of the
 * chain, so every recorded header is exactly what the library decided to send.
 */
async function sendThroughDefaultChain(location: string, extra: Record<string, string>): Promise<ReturnType<typeof recorder>["calls"]> {
	const rec = recorder([redirect(location, 302), ok()]);
	const httpClient = KiotaClientFactory.create(rec.fetchFn);
	const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
	await adapter.sendNoResponseContent(requestInformation("https://api.example.com/v1/me", extra), undefined);
	return rec.calls;
}

const WITH_COOKIE: Record<string, string> = { Cookie: COOKIE, "X-Trace": TRACE };

function expectBearerAndCookieDropped(calls: ReturnType<typeof recorder>["calls"]) {
	const first = calls[0];
	const followUp = calls[calls.length - 1];
	// The addressed request carries them; the request to the other origin must not.
	expect(hasHeader(first.headers, "authorization")).toBe(true);
	if (hasHeader(first.headers, "cookie")) {
		expect(hasHeader(followUp.headers, "cookie")).toBe(false);
	}
	expect(hasHeader(followUp.headers, "authorization")).toBe(false);
	expect(hasHeader(followUp.headers, "cookie")).toBe(false);
}

describe("cross-origin redirect drops the bearer token and the cookie", () => {
	const cases: Array<[string, string, string]> = [
		["different host, same scheme", "https://collector.example/ingest", "https://collector.example/ingest"],
		["different port", "https://api.example.com:8443/collect", "https://api.example.com:8443/collect"],
		["different scheme, same host", "http://api.example.com/collect", "http://api.example.com/collect"],
	];

	for (const [name, location, expectedUrl] of cases) {
		it(name, async () => {
			const calls = await sendThroughDefaultChain(location, WITH_COOKIE);
			expect(calls).toHaveLength(2);
			expect(calls[0].url).toBe("https://api.example.com/v1/me");
			expect(calls[1].url).toBe(expectedUrl);
			expectBearerAndCookieDropped(calls);
		});
	}

	it("the cookie is removed as well as the bearer token", async () => {
		const calls = await sendThroughDefaultChain("https://collector.example/ingest", WITH_COOKIE);
		const followUp = calls[calls.length - 1];
		expect(hasHeader(followUp.headers, "cookie")).toBe(false);
		expect(followUp.headers["X-Trace"] ?? followUp.headers["x-trace"]).toBe(TRACE);
	});

	it("mixed-case caller spellings are still removed", async () => {
		const calls = await sendThroughDefaultChain("https://collector.example/ingest", {
			AUTHORIZATION: "Bearer TOKEN",
			Cookie: COOKIE,
		});
		expectBearerAndCookieDropped(calls);
	});

	it("each hop of a redirect chain is scrubbed", async () => {
		const rec = recorder([redirect("https://first.example/a", 301), redirect("https://second.example/b", 307), ok()]);
		const httpClient = KiotaClientFactory.create(rec.fetchFn);
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
		await adapter.sendNoResponseContent(requestInformation("https://api.example.com/v1/me", WITH_COOKIE), undefined);
		expect(rec.calls.map((c) => c.url)).toEqual(["https://api.example.com/v1/me", "https://first.example/a", "https://second.example/b"]);
		expect(hasHeader(rec.calls[1].headers, "authorization")).toBe(false);
		expect(hasHeader(rec.calls[1].headers, "cookie")).toBe(false);
		expect(hasHeader(rec.calls[2].headers, "authorization")).toBe(false);
		expect(hasHeader(rec.calls[2].headers, "cookie")).toBe(false);
	});
});
