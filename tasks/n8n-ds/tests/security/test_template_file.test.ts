import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { makeExecuteContext } from '../support/context';
import { makeMarkerFile } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const currentSend = new EmailSend().getNodeType(2.1);

let smtp: SmtpServer | undefined;

afterEach(async () => {
	await smtp?.close();
	smtp = undefined;
});

async function sendWithTemplate(template: unknown) {
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
			emailFormat: 'html',
			options: { appendAttribution: false, htmlTemplate: template },
			text: '',
			html: '<p>Original body</p>',
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

describe('Send Email, current version: a template value that names host content', () => {
	it('does not load a local file as the HTML body', async () => {
		const marker = makeMarkerFile('template-path');
		const { mail } = await sendWithTemplate(marker.file);

		expect(mail).not.toContain(marker.content);
	});
});
