import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { Gmail } from '../../../nodes/Google/Gmail/Gmail.node';
import { decodeGmailRaw, makeExecuteContext } from '../support/context';
import { base64Of } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const currentSend = new EmailSend().getNodeType(2.1);
const currentGmail = new Gmail().getNodeType(2.2);

let smtp: SmtpServer | undefined;

afterEach(async () => {
	await smtp?.close();
	smtp = undefined;
});

function withoutSoftBreaks(text: string) {
	return text.replace(/=\r\n/g, '').replace(/=\n/g, '');
}

describe('Send Email, current version: template values', () => {
	it('delivers a template given as HTML text', async () => {
		smtp = await startSmtpServer();
		const context = makeExecuteContext(
			{
				operation: 'send',
				fromEmail: 'sender@example.com',
				toEmail: 'recipient@example.com',
				subject: 'Report',
				emailFormat: 'html',
				options: { appendAttribution: false, htmlTemplate: '<p>From the template</p>' },
				text: '',
				html: '<p>Original body</p>',
			},
			{
				typeVersion: 2.1,
				credentials: { host: smtp.host, port: smtp.port, secure: false },
			},
		);

		await currentSend.execute.call(context);

		expect(withoutSoftBreaks(smtp.allText())).toContain('From the template');
	});
});

describe('Gmail, current implementation: legitimate use', () => {
	it('sends a message with a binary attachment', async () => {
		const attachmentBytes = 'gmail-attachment-bytes';
		const requests: Array<Record<string, any>> = [];
		const context = makeExecuteContext(
			{
				resource: 'message',
				operation: 'send',
				authentication: 'oAuth2',
				sendTo: 'recipient@example.com',
				subject: 'Mail with an attachment',
				emailType: 'text',
				message: 'See the attached report',
				options: {
					appendAttribution: false,
					attachmentsUi: { attachmentsBinary: [{ property: 'report' }] },
				},
			},
			{
				typeVersion: 2.2,
				items: [
					{
						json: {},
						binary: {
							report: {
								data: base64Of(attachmentBytes),
								mimeType: 'text/plain',
								fileName: 'report.txt',
							},
						},
					},
				],
				onHttpRequest: async (requestOptions) => {
					requests.push(requestOptions);
					return { id: 'test-message', threadId: 'test-thread' };
				},
			},
		);

		await currentGmail.execute.call(context);

		expect(requests).toHaveLength(1);
		const raw = decodeGmailRaw(requests[0].body.raw);
		expect(raw).toContain('See the attached report');
		expect(raw).toContain('report.txt');
		expect(raw).toContain(base64Of(attachmentBytes));
	});
});
