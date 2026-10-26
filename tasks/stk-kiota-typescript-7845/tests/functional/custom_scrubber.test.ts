import { describe, expect, it } from "vitest";

import { FetchRequestAdapter, KiotaClientFactory, RedirectHandlerOptions } from "@product/fetch";

import { authProvider, COOKIE, hasHeader, ok, PROXY, recorder, redirect, requestInformation } from "../support/helpers";

/**
 * A caller may install its own policy for which headers to remove on a redirect. The library must
 * use that policy rather than its own default, so a policy that keeps a header keeps it.
 */
describe("a caller-supplied redirect policy is honoured", () => {
	it("the custom callback runs and its decision stands", async () => {
		let invoked = 0;
		const custom = (headers: Record<string, string>, originalUrl: string, newUrl: string): void => {
			invoked++;
			headers["X-Custom-Scrub"] = `${originalUrl.length > 0 && newUrl.length > 0 ? "ran" : "missing"}`;
		};

		const rec = recorder([redirect("https://collector.example/ingest", 302), ok()]);
		const httpClient = KiotaClientFactory.create(rec.fetchFn);
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
		const ri = requestInformation("https://api.example.com/v1/me", {
			Cookie: COOKIE,
			"Proxy-Authorization": PROXY,
		});
		ri.addRequestOptions([new RedirectHandlerOptions({ scrubSensitiveHeaders: custom })]);

		await adapter.sendNoResponseContent(ri, undefined);

		expect(invoked).toBe(1);
		expect(rec.calls).toHaveLength(2);
		const followUp = rec.calls[1];
		expect(hasHeader(followUp.headers, "authorization")).toBe(true);
		expect(hasHeader(followUp.headers, "cookie")).toBe(true);
		expect(hasHeader(followUp.headers, "proxy-authorization")).toBe(true);
		expect(followUp.headers["X-Custom-Scrub"]).toBe("ran");
	});

	it("the default policy is not applied over the caller's choice", async () => {
		const custom = (): void => {
			/* deliberately keep every header */
		};
		const rec = recorder([redirect("http://api.example.com/collect", 302), ok()]);
		const httpClient = KiotaClientFactory.create(rec.fetchFn);
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
		const ri = requestInformation("https://api.example.com/v1/me");
		ri.addRequestOptions([new RedirectHandlerOptions({ scrubSensitiveHeaders: custom })]);
		await adapter.sendNoResponseContent(ri, undefined);
		expect(hasHeader(rec.calls[1].headers, "authorization")).toBe(true);
	});
});
