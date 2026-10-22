import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { Gmail } from '../../../nodes/Google/Gmail/Gmail.node';
import { decodeGmailRaw, makeExecuteContext } from '../support/context';
import { base64Of } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const legacySend = new EmailSend().getNodeType(1);
const legacyGmail = new Gmail().getNodeType(1);

let smtp: SmtpServer | undefined;

afterEach(async () => {
	await smtp?.close();
	smtp = undefined;
});

function withoutSoftBreaks(text: string) {
	return text.replace(/=\r\n/g, '').replace(/=\n/g, '');
}

describe('Send Email, first implementation: legitimate use', () => {
	it('sends text, HTML and a binary attachment', async () => {
		smtp = await startSmtpServer();
		const attachmentBytes = 'legacy-attachment-bytes';
		const context = makeExecuteContext(
			{
				fromEmail: 'sender@example.com',
				toEmail: 'recipient@example.com',
				ccEmail: '',
				bccEmail: '',
				subject: 'Legacy message',
				text: 'Legacy plain body',
				html: '<p>Legacy HTML body</p>',
				attachments: 'report',
				options: {},
			},
			{
				typeVersion: 1,
				credentials: { host: smtp.host, port: smtp.port, secure: false },
				items: [
					{
						json: {},
						binary: {
							report: {
								data: base64Of(attachmentBytes),
								mimeType: 'text/plain',
								fileName: 'notes.txt',
							},
						},
					},
				],
			},
		);

		await legacySend.execute.call(context);

		const readable = withoutSoftBreaks(smtp.allText());
		expect(readable).toContain('Legacy plain body');
		expect(readable).toContain('<p>Legacy HTML body</p>');
		expect(readable).toContain('notes.txt');
		expect(smtp.allText()).toContain(base64Of(attachmentBytes));
	});
});

describe('Gmail, first implementation: legitimate use', () => {
	it('sends a message built from string fields', async () => {
		const requests: Array<Record<string, any>> = [];
		const context = makeExecuteContext(
			{
				resource: 'message',
				operation: 'send',
				authentication: 'oAuth2',
				additionalFields: {},
				toList: ['recipient@example.com'],
				subject: 'Gmail subject',
				message: 'Gmail plain body',
				includeHtml: true,
				htmlMessage: '<p>Gmail HTML body</p>',
			},
			{
				typeVersion: 1,
				onHttpRequest: async (requestOptions) => {
					requests.push(requestOptions);
					return { id: 'test-message' };
				},
			},
		);

		await legacyGmail.execute.call(context);

		expect(requests).toHaveLength(1);
		const raw = decodeGmailRaw(requests[0].body.raw);
		expect(raw).toContain('Gmail subject');
		expect(raw).toContain('Gmail plain body');
		expect(raw).toContain('<p>Gmail HTML body</p>');
	});
});
