import { describe, expect, it } from "vitest";

import { FetchRequestAdapter, HttpClient } from "@product/fetch";

import { authProvider, COOKIE, credentialKeys, ok, PROXY, TOKEN } from "../support/helpers";
import { HttpMethod, RequestInformation } from "@microsoft/kiota-abstractions";

const ADDRESSED = "https://api.example.com/v1/me";

/**
 * A caller's own transport: it follows redirects by default and forwards the headers it was given,
 * like a low-level HTTP client. It honours the redirect policy on the request: "manual" returns the
 * redirect response without sending it anywhere, and "error" refuses. A request that carries a
 * credential for the addressed origin must not be handed to this transport in a state where it can
 * follow a redirect to another origin.
 */
class FollowingTransport {
	public readonly seen: Array<{ url: string; headers: Record<string, string>; policy?: unknown }> = [];

	public constructor(private readonly target: string) {}

	public async fetch(url: string, init: any): Promise<Response> {
		const policy = init?.redirect;
		this.seen.push({ url, headers: { ...(init?.headers ?? {}) }, policy });
		if (policy === "manual") {
			return new Response(null, { status: 302, headers: { Location: this.target } });
		}
		if (policy === "error") {
			throw new Error("a redirect was refused");
		}
		this.seen.push({ url: this.target, headers: { ...(init?.headers ?? {}) }, policy: "followed" });
		return ok();
	}

	public followUps(): Array<{ url: string; headers: Record<string, string>; policy?: unknown }> {
		return this.seen.filter((call) => call.url === this.target);
	}
}

async function prepare(extra: Record<string, string> = {}): Promise<{ init: any; transport: FollowingTransport }> {
	const ri = new RequestInformation();
	ri.URL = ADDRESSED;
	ri.httpMethod = HttpMethod.GET;
	for (const [name, value] of Object.entries(extra)) {
		ri.headers.add(name, value);
	}
	const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, new HttpClient(async () => ok()));
	const init: any = await adapter.convertToNativeRequest(ri);
	const transport = new FollowingTransport("https://collector.example/ingest");
	try {
		await transport.fetch(ADDRESSED, init);
	} catch {
		// A transport that refuses to follow is an acceptable outcome: nothing reached the target.
	}
	return { init, transport };
}

describe("a request prepared for the caller cannot follow a cross-origin redirect with credentials", () => {
	it("cross-host redirect does not deliver the bearer token", async () => {
		const { transport } = await prepare();
		expect(transport.followUps().filter((c) => credentialKeys(c.headers).length > 0)).toEqual([]);
	});

	it("cross-host redirect does not deliver any credential header", async () => {
		const { transport } = await prepare({ Authorization: `Bearer ${TOKEN}`, Cookie: COOKIE, "Proxy-Authorization": PROXY });
		expect(transport.followUps().filter((c) => credentialKeys(c.headers).length > 0)).toEqual([]);
	});

	it("scheme change does not deliver the credentials", async () => {
		const adapter = new FetchRequestAdapter(authProvider(), undefined, undefined, new HttpClient(async () => ok()));
		const ri = new RequestInformation();
		ri.URL = "http://api.example.com/v1/me";
		ri.httpMethod = HttpMethod.GET;
		const init: any = await adapter.convertToNativeRequest(ri);
		const transport = new FollowingTransport("https://api.example.com/collect");
		try {
			await transport.fetch(ri.URL, init);
		} catch {
			// refused is fine
		}
		expect(transport.followUps().filter((c) => credentialKeys(c.headers).length > 0)).toEqual([]);
	});
});
