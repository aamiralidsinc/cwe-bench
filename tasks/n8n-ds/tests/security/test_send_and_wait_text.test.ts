import { SEND_AND_WAIT_OPERATION } from 'n8n-workflow';
import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { makeExecuteContext } from '../support/context';
import { startHttpRecorder, type HttpRecorder } from '../support/http-recorder';
import { makeMarkerFile } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const sendAndWaitNode = new EmailSend().getNodeType(2.1);

let smtp: SmtpServer | undefined;
let recorder: HttpRecorder | undefined;

afterEach(async () => {
	await recorder?.close();
	recorder = undefined;
	await smtp?.close();
	smtp = undefined;
});

async function waitSendOnce(optionOverrides: Record<string, unknown>) {
	if (smtp) {
		await smtp.close();
		smtp = undefined;
	}
	smtp = await startSmtpServer();
	const context = makeExecuteContext(
		{
			operation: SEND_AND_WAIT_OPERATION,
			fromEmail: 'sender@example.com',
			toEmail: 'recipient@example.com',
			message: 'Please approve this request',
			subject: 'Approval needed',
			'approvalOptions.values': { approvalType: 'single' },
			options: { appendAttribution: false, ...optionOverrides },
			responseType: 'approval',
			'options.limitWaitTime.values': {},
		},
		{
			typeVersion: 2.1,
			credentials: { host: smtp.host, port: smtp.port, secure: false },
		},
	);

	let failure: unknown;
	try {
		await sendAndWaitNode.execute.call(context);
	} catch (error) {
		failure = error;
	}
	return { failure, mail: smtp.allText() };
}

describe('Send Email, wait-for-response operation: alternative message values', () => {
	it('does not put a local file into the plain-text alternative', async () => {
		const marker = makeMarkerFile('wait-text');
		const { mail } = await waitSendOnce({ plainText: { path: marker.file } });

		expect(mail).not.toContain(marker.content);
	});

	it('does not fetch a URL for the plain-text alternative', async () => {
		const marker = makeMarkerFile('wait-href');
		recorder = await startHttpRecorder(marker.content);
		const { mail } = await waitSendOnce({ plainText: { href: `${recorder.baseUrl}/alt.txt` } });

		expect(recorder.requests).toHaveLength(0);
		expect(mail).not.toContain(marker.content);
	});
});
