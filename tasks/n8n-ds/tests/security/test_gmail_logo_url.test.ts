import { afterEach, describe, expect, it } from 'vitest';

import { Gmail } from '../../../nodes/Google/Gmail/Gmail.node';
import { decodeGmailRaw, makeExecuteContext } from '../support/context';
import { startHttpRecorder, type HttpRecorder } from '../support/http-recorder';
import { base64Of, makeMarkerFile } from '../support/markers';

const currentGmail = new Gmail().getNodeType(2.2);

let recorder: HttpRecorder | undefined;

afterEach(async () => {
	await recorder?.close();
	recorder = undefined;
});

async function sendCurrentGmail(options: Record<string, unknown>) {
	const requests: Array<Record<string, any>> = [];
	const context = makeExecuteContext(
		{
			resource: 'message',
			operation: 'send',
			authentication: 'oAuth2',
			sendTo: 'recipient@example.com',
			subject: 'Mail from the workflow',
			emailType: 'text',
			message: 'Workflow message',
			options,
		},
		{
			typeVersion: 2.2,
			onHttpRequest: async (requestOptions) => {
				requests.push(requestOptions);
				return { id: 'test-message', threadId: 'test-thread' };
			},
		},
	);

	let failure: unknown;
	try {
		await currentGmail.execute.call(context);
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

	return { failure, raw };
}

describe('Gmail, current implementation: an image address supplied by the workflow', () => {
	it('does not fetch a remote address and put the response into the message', async () => {
		const marker = makeMarkerFile('gmail-logo');
		recorder = await startHttpRecorder(marker.content);
		const { raw } = await sendCurrentGmail({
			appendAttribution: false,
			logoUrl: `${recorder.baseUrl}/logo.png`,
		});

		expect(recorder.requests).toHaveLength(0);
		expect(raw).not.toContain(marker.content);
		expect(raw).not.toContain(base64Of(marker.content));
	});
});
