import { describe, expect, it } from "vitest";

import { ResponseHandlerOption } from "@microsoft/kiota-abstractions";
import { FetchRequestAdapter, KiotaClientFactory } from "@product/fetch";

import { authProvider, hasHeader, ok, recorder, redirect, requestInformation, TRACE } from "../support/helpers";

/**
 * A cross-origin redirect is followed as today; the request is not refused and its response is
 * the one handed back to the caller. Only the credential headers are withheld.
 */
describe("a cross-origin redirect still completes", () => {
	it("returns the final response and sends the follow-up request", async () => {
		const rec = recorder([redirect("https://collector.example/ingest", 302), ok("final-body")]);
		const httpClient = KiotaClientFactory.create(rec.fetchFn);
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
		const ri = requestInformation("https://api.example.com/v1/me", { "X-Trace": TRACE });
		const option = new ResponseHandlerOption();
		option.responseHandler = {
			handleResponse: async (response: Response) => ({ status: response.status, body: await response.text() }),
		} as any;
		ri.addRequestOptions([option]);
		const result: any = await adapter.sendNoResponseContent(ri, undefined);
		expect(rec.calls).toHaveLength(2);
		expect(result.status).toBe(200);
		expect(result.body).toBe("final-body");
	});

	it("keeps non-credential headers on the follow-up request", async () => {
		const rec = recorder([redirect("https://collector.example/ingest", 301), ok()]);
		const httpClient = KiotaClientFactory.create(rec.fetchFn);
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, httpClient);
		await adapter.sendNoResponseContent(
			requestInformation("https://api.example.com/v1/me", { "X-Trace": TRACE, Accept: "application/json" }),
			undefined,
		);
		const followUp = rec.calls[1];
		expect(followUp.headers["X-Trace"] ?? followUp.headers["x-trace"]).toBe(TRACE);
		expect(followUp.headers["Accept"] ?? followUp.headers["accept"]).toBe("application/json");
		expect(hasHeader(followUp.headers, "x-trace")).toBe(true);
	});
});
