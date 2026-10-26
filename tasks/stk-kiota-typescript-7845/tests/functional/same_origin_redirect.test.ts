import { describe, expect, it } from "vitest";

import { FetchRequestAdapter, KiotaClientFactory } from "@product/fetch";

import { authProvider, COOKIE, hasHeader, ok, PROXY, recorder, redirect, requestInformation } from "../support/helpers";

/**
 * Same-host, same-scheme redirects, including relative references, are ordinary request handling:
 * every header the caller attached must still be there on the follow-up request.
 */
async function send(location: string): Promise<ReturnType<typeof recorder>["calls"]> {
	const rec = recorder([redirect(location, 302), ok()]);
	const httpClient = KiotaClientFactory.create(rec.fetchFn);
	const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
	await adapter.sendNoResponseContent(
		requestInformation("https://api.example.com/v1/me", {
			Cookie: COOKIE,
			"Proxy-Authorization": PROXY,
			"X-Trace": "trace-123",
		}),
		undefined,
	);
	return rec.calls;
}

describe("a redirect that stays on the same origin keeps every header", () => {
	const cases: Array<[string, string, string]> = [
		["absolute same-origin path", "https://api.example.com/v2/me", "https://api.example.com/v2/me"],
		["relative path", "/v2/me", "https://api.example.com/v2/me"],
		["protocol-relative path", "//api.example.com/v2/me", "https://api.example.com/v2/me"],
		["relative query", "?page=2", "https://api.example.com/v1/me?page=2"],
	];

	for (const [name, location, expectedUrl] of cases) {
		it(name, async () => {
			const calls = await send(location);
			expect(calls).toHaveLength(2);
			expect(calls[1].url).toBe(expectedUrl);
			expect(hasHeader(calls[1].headers, "authorization")).toBe(true);
			expect(hasHeader(calls[1].headers, "cookie")).toBe(true);
			expect(hasHeader(calls[1].headers, "proxy-authorization")).toBe(true);
			expect(calls[1].headers["X-Trace"] ?? calls[1].headers["x-trace"]).toBe("trace-123");
		});
	}
});
