import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { makeExecuteContext } from '../support/context';
import { startHttpRecorder, type HttpRecorder } from '../support/http-recorder';
import { base64Of, makeMarkerFile } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const currentSend = new EmailSend().getNodeType(2.1);

let smtp: SmtpServer | undefined;
let recorder: HttpRecorder | undefined;

afterEach(async () => {
	await recorder?.close();
	recorder = undefined;
	await smtp?.close();
	smtp = undefined;
});

async function sendWithAttachments(overrides: Record<string, unknown>) {
	if (smtp) {
		await smtp.close();
		smtp = undefined;
	}
	smtp = await startSmtpServer();
	const context = makeExecuteContext(
		{
			operation: 'send',
			fromEmail: 'sender@example.com',
			toEmail: 'recipient@example.com',
			subject: 'Report',
			emailFormat: 'text',
			options: { appendAttribution: false },
			text: 'See attached',
			html: '',
			...overrides,
		},
		{
			typeVersion: 2.1,
			credentials: { host: smtp.host, port: smtp.port, secure: false },
		},
	);

	let failure: unknown;
	try {
		await currentSend.execute.call(context);
	} catch (error) {
		failure = error;
	}
	return { failure, mail: smtp.allText() };
}

describe('Send Email, current version: attachment sources from workflow values', () => {
	it('does not attach a local file given by path', async () => {
		const marker = makeMarkerFile('attach-path');
		const { mail } = await sendWithAttachments({
			options: { appendAttribution: false, attachmentPaths: marker.file },
		});

		expect(mail).not.toContain(marker.content);
		expect(mail).not.toContain(base64Of(marker.content));
		expect(mail).not.toContain(base64Of(`${marker.content}\n`));
	});

	it('does not fetch and attach a URL', async () => {
		const marker = makeMarkerFile('attach-href');
		recorder = await startHttpRecorder(marker.content);
		const { mail } = await sendWithAttachments({
			options: { appendAttribution: false, attachmentPaths: `${recorder.baseUrl}/report.txt` },
		});

		expect(recorder.requests).toHaveLength(0);
		expect(mail).not.toContain(marker.content);
		expect(mail).not.toContain(base64Of(marker.content));
	});
});
