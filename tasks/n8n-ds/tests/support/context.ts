import http from 'node:http';
import https from 'node:https';

import type { IBinaryData, IExecuteFunctions } from 'n8n-workflow';

/**
 * A real HTTP request for helpers.httpRequest, so a value that names a remote
 * address reaches the loopback recorder exactly as the product would reach a
 * real server. The recorder allows loopback connections through nock.
 */
function directHttpRequest(requestOptions: Record<string, any>): Promise<unknown> {
	const url = new URL(String(requestOptions.url ?? requestOptions.uri));
	const client = url.protocol === 'https:' ? https : http;
	return new Promise((resolve, reject) => {
		const request = client.request(
			url,
			{ method: requestOptions.method ?? 'GET', headers: requestOptions.headers },
			(response) => {
				const chunks: Buffer[] = [];
				response.on('data', (chunk: Buffer) => chunks.push(chunk));
				response.on('end', () => {
					const body = Buffer.concat(chunks);
					if (requestOptions.encoding === 'arraybuffer') {
						resolve(
							body.buffer.slice(body.byteOffset, body.byteOffset + body.byteLength) as ArrayBuffer,
						);
					} else {
						resolve(body.toString('utf8'));
					}
				});
			},
		);
		request.on('error', reject);
		request.end();
	});
}

export type ExecuteContextOptions = {
	nodeName?: string;
	typeVersion?: number;
	instanceId?: string;
	items?: Array<Record<string, unknown>>;
	credentials?: Record<string, unknown>;
	signedResumeUrl?: string;
	/** Called for every outbound authenticated HTTP request the node makes. */
	onHttpRequest?: (requestOptions: Record<string, any>) => Promise<unknown>;
};

/**
 * The execution context the workflow engine hands a node. Parameters are read
 * from the given map, falling back to the caller's default exactly like the
 * real implementation; helper methods are the only things stubbed, because the
 * transport (SMTP / HTTP) is real in these tests.
 */
export function makeExecuteContext(
	params: Record<string, unknown>,
	options: ExecuteContextOptions = {},
) {
	const items = (options.items ?? [{ json: {} }]) as any[];

	const ctx = {
		getInputData: () => items,
		getNode: () => ({ name: options.nodeName ?? 'test-node', typeVersion: options.typeVersion ?? 2.1 }),
		getInstanceId: () => options.instanceId ?? 'test-instance',
		getCredentials: async () => options.credentials ?? {},
		getNodeParameter: (name: string, _itemIndex: number, fallback?: unknown) =>
			Object.prototype.hasOwnProperty.call(params, name) ? params[name] : fallback,
		continueOnFail: () => false,
		putExecutionToWait: async () => undefined,
		getSignedResumeUrl: () =>
			options.signedResumeUrl ??
			'http://localhost/waiting-webhook/node?approved=true&signature=abc',
		helpers: {
			assertBinaryData: (itemIndex: number, propertyName: string) => {
				const binary = items[itemIndex]?.binary as Record<string, IBinaryData> | undefined;
				if (!binary?.[propertyName]) throw new Error(`missing binary ${propertyName}`);
				return binary[propertyName];
			},
			getBinaryDataBuffer: async (itemIndex: number, propertyName: string) => {
				const binary = items[itemIndex]?.binary as Record<string, IBinaryData> | undefined;
				return Buffer.from(binary?.[propertyName]?.data ?? '', 'base64');
			},
			requestWithAuthentication: async (
				_credentialType: string,
				requestOptions: Record<string, any>,
			) => {
				if (options.onHttpRequest) return options.onHttpRequest(requestOptions);
				return {};
			},
			httpRequest: async (requestOptions: Record<string, any>) =>
				directHttpRequest(requestOptions),
			returnJsonArray: (data: unknown) => {
				const entries = Array.isArray(data) ? data : [data];
				return entries.map((json) => ({ json }));
			},
			constructExecutionMetaData: (data: Array<Record<string, unknown>>, meta?: any) =>
				data.map((entry) => ({ ...entry, pairedItem: meta?.itemData })),
		},
	};

	return ctx as unknown as IExecuteFunctions;
}

/** Decode the URL-safe base64 payload the Gmail node stores in `raw`. */
export function decodeGmailRaw(raw: string): string {
	const base64 = raw.replace(/-/g, '+').replace(/_/g, '/');
	return Buffer.from(base64, 'base64').toString('utf8');
}
