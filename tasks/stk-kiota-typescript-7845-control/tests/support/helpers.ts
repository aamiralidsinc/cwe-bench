/**
 * Shared helpers for the hidden suites. No product code is used to compute an expected value:
 * the expected credential set is a literal list, and every call record is a plain copy.
 */
import { BaseBearerTokenAuthenticationProvider, HttpMethod, RequestInformation } from "@microsoft/kiota-abstractions";

export type Call = {
	url: string;
	headers: Record<string, string>;
	redirect?: unknown;
	method?: unknown;
	body?: unknown;
};

/** A fetch stand-in that queues responses and records exactly what the library passed it. */
export function recorder(responses: Response[]) {
	const calls: Call[] = [];
	const fetchFn = async (url: string, init?: any): Promise<Response> => {
		calls.push({
			url,
			headers: { ...(init?.headers ?? {}) },
			redirect: init?.redirect,
			method: init?.method,
			body: init?.body,
		});
		const next = responses.shift();
		return next ?? new Response("ok", { status: 200 });
	};
	return { fetchFn, calls };
}

export const TOKEN = "TEST-TOKEN";
export const COOKIE = "session=SECRET";
export const PROXY = "Basic SECRET";
export const TRACE = "trace-123";

export function authProvider(token: string = TOKEN): BaseBearerTokenAuthenticationProvider {
	return new BaseBearerTokenAuthenticationProvider({
		getAuthorizationToken: async () => token,
		getAllowedHostsValidator: () => ({ isValidHost: () => true, getValidHosts: () => [] }),
	} as any);
}

export function requestInformation(url = "https://api.example.com/v1/me", extra: Record<string, string> = {}): RequestInformation {
	const ri = new RequestInformation();
	ri.URL = url;
	ri.httpMethod = HttpMethod.GET;
	for (const [name, value] of Object.entries(extra)) {
		ri.headers.add(name, value);
	}
	return ri;
}

/** Case-insensitive header lookup, returning the value of any spelling. */
export function headerValue(headers: Record<string, string>, name: string): string | undefined {
	const wanted = name.toLowerCase();
	for (const [key, value] of Object.entries(headers)) {
		if (key.toLowerCase() === wanted) return value;
	}
	return undefined;
}

export function hasHeader(headers: Record<string, string>, name: string): boolean {
	return headerValue(headers, name) !== undefined;
}

export const CREDENTIAL_HEADERS = ["authorization", "cookie", "proxy-authorization"] as const;

/** Every credential header spelling present in a recorded header map. */
export function credentialKeys(headers: Record<string, string>): string[] {
	return Object.keys(headers).filter((key) => (CREDENTIAL_HEADERS as readonly string[]).includes(key.toLowerCase()));
}

export function redirect(location: string, status = 302): Response {
	return new Response(null, { status, headers: { Location: location } });
}

export function ok(body = "ok"): Response {
	return new Response(body, { status: 200 });
}
