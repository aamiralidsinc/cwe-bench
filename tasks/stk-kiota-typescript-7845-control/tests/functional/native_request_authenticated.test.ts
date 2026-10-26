import { describe, expect, it } from "vitest";

import { HttpMethod, RequestInformation } from "@microsoft/kiota-abstractions";
import { FetchRequestAdapter, HttpClient } from "@product/fetch";

import { authProvider, hasHeader, ok } from "../support/helpers";

/**
 * Preparing a request for the caller is documented to hand back the fully prepared native request.
 * It must keep its method, body and attached credentials; only the redirect policy may differ.
 */
describe("the prepared native request stays authenticated", () => {
	function makeRequest(): RequestInformation {
		const ri = new RequestInformation();
		ri.URL = "https://api.example.com/v1/me";
		ri.httpMethod = HttpMethod.POST;
		(ri as any).content = "payload";
		return ri;
	}

	it("keeps method, body and the bearer token", async () => {
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, new HttpClient(async () => ok()));
		const init: any = await adapter.convertToNativeRequest(makeRequest());
		expect(init.method).toBe("POST");
		expect(init.body).toBe("payload");
		expect(hasHeader(init.headers, "authorization")).toBe(true);
	});

	it("is usable as-is for a normal request to the addressed origin", async () => {
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, new HttpClient(async () => ok()));
		const ri = makeRequest();
		const init: any = await adapter.convertToNativeRequest(ri);
		const seen: Array<{ url: string; headers: Record<string, string> }> = [];
		await (async (url: string, options: any) => {
			seen.push({ url, headers: { ...(options?.headers ?? {}) } });
			return ok();
		})(ri.URL, init);
		expect(seen).toHaveLength(1);
		expect(seen[0].url).toBe("https://api.example.com/v1/me");
		expect(hasHeader(seen[0].headers, "authorization")).toBe(true);
	});
});
