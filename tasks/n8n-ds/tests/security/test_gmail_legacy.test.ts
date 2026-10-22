import { afterEach, describe, expect, it } from 'vitest';

import { Gmail } from '../../../nodes/Google/Gmail/Gmail.node';
import { decodeGmailRaw, makeExecuteContext } from '../support/context';
import { startHttpRecorder, type HttpRecorder } from '../support/http-recorder';
import { makeMarkerFile } from '../support/markers';

const legacyGmail = new Gmail().getNodeType(1);

let recorder: HttpRecorder | undefined;

afterEach(async () => {
	await recorder?.close();
	recorder = undefined;
});

async function runLegacyGmail(params: Record<string, unknown>) {
	const requests: Array<Record<string, any>> = [];
	const base: Record<string, unknown> = {
		resource: 'message',
		operation: 'send',
		authentication: 'oAuth2',
		additionalFields: {},
		toList: ['recipient@example.com'],
		subject: 'Mail from the workflow',
		message: 'plain body',
		includeHtml: false,
		htmlMessage: '',
		...params,
	};
	const context = makeExecuteContext(base, {
		typeVersion: 1,
		onHttpRequest: async (requestOptions) => {
			requests.push(requestOptions);
			return { id: 'test-message', threadId: 'test-thread' };
		},
	});

	let failure: unknown;
	try {
		await legacyGmail.execute.call(context);
	} catch (error) {
		failure = error;
	}

	const raw = requests
		.map((request) => {
			if (typeof request.body?.raw === 'string') return decodeGmailRaw(request.body.raw);
			if (typeof request.body?.message?.raw === 'string') {
				return decodeGmailRaw(request.body.message.raw);
			}
			return '';
		})
		.join('\n');

	return { failure, raw, requestCount: requests.length };
}

async function runLegacyGmailReply(message: unknown) {
	const requests: Array<Record<string, any>> = [];
	const context = makeExecuteContext(
		{
			resource: 'message',
			operation: 'reply',
			authentication: 'oAuth2',
			messageId: 'previous-message',
			additionalFields: {},
			toList: ['recipient@example.com'],
			subject: 'Mail from the workflow',
			message,
			includeHtml: false,
			htmlMessage: '',
		},
		{
			typeVersion: 1,
			onHttpRequest: async (requestOptions) => {
				requests.push(requestOptions);
				if (String(requestOptions.method).toUpperCase() === 'GET') {
					return {
						payload: {
							headers: [
								{ name: 'From', value: 'sender@example.com' },
								{ name: 'Subject', value: 'Previous subject' },
								{ name: 'Message-ID', value: '<previous@example.com>' },
								{ name: 'References', value: '<previous@example.com>' },
							],
						},
					};
				}
				return { id: 'test-message', threadId: 'test-thread' };
			},
		},
	);

	let failure: unknown;
	try {
		await legacyGmail.execute.call(context);
	} catch (error) {
		failure = error;
	}

	const raw = requests
		.map((request) => {
			if (typeof request.body?.raw === 'string') return decodeGmailRaw(request.body.raw);
			if (typeof request.body?.message?.raw === 'string') {
				return decodeGmailRaw(request.body.message.raw);
			}
			return '';
		})
		.join('\n');

	return { failure, raw, requestCount: requests.length };
}

describe('Gmail, first implementation: message values that name content', () => {
	it('does not put a local file into a sent message', async () => {
		const marker = makeMarkerFile('gmail-path');
		const { raw } = await runLegacyGmail({ message: { path: marker.file } });

		expect(raw).not.toContain(marker.content);
	});

	it('does not fetch a URL for the HTML body of a created draft', async () => {
		const marker = makeMarkerFile('gmail-draft-href');
		recorder = await startHttpRecorder(marker.content);
		const { raw } = await runLegacyGmail({
			resource: 'draft',
			operation: 'create',
			additionalFields: { toList: ['recipient@example.com'] },
			includeHtml: true,
			htmlMessage: { href: `${recorder.baseUrl}/draft-body.txt` },
		});

		expect(recorder.requests).toHaveLength(0);
		expect(raw).not.toContain(marker.content);
	});

	it('does not fetch a URL for the body of a reply', async () => {
		const marker = makeMarkerFile('gmail-reply-href');
		recorder = await startHttpRecorder(marker.content);
		const { raw } = await runLegacyGmailReply({
			href: `${recorder.baseUrl}/reply-body.txt`,
		});

		expect(recorder.requests).toHaveLength(0);
		expect(raw).not.toContain(marker.content);
	});
});
