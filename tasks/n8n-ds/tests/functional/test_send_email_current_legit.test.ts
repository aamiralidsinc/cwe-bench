import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { smtpConnectionTest } from '../../../nodes/EmailSend/v2/utils';
import { makeExecuteContext } from '../support/context';
import { decodeTextBody } from '../support/mime';
import { base64Of } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const currentSend = new EmailSend().getNodeType(2.1);

let smtp: SmtpServer | undefined;

afterEach(async () => {
	await smtp?.close();
	smtp = undefined;
});

function withoutSoftBreaks(text: string) {
	return text.replace(/=\r\n/g, '').replace(/=\n/g, '');
}

async function sendOnce(
	params: Record<string, unknown>,
	options: { items?: Array<Record<string, unknown>>; typeVersion?: number } = {},
) {
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
			subject: 'Quarterly report',
			emailFormat: 'text',
			options: { appendAttribution: false },
			text: 'Plain body text',
			html: '<p>HTML body text</p>',
			...params,
		},
		{
			typeVersion: options.typeVersion ?? 2.1,
			items: options.items,
			credentials: { host: smtp.host, port: smtp.port, secure: false },
		},
	);

	const result = await currentSend.execute.call(context);
	return { result, mail: smtp.allText(), message: smtp.messages[0] };
}

describe('Send Email, current version: legitimate use', () => {
	it('sends a plain-text message and appends the attribution by default', async () => {
		const { mail } = await sendOnce({
			emailFormat: 'text',
			options: {},
			text: 'Plain body text for the team',
		});

		const readable = withoutSoftBreaks(mail);
		expect(readable).toContain('Plain body text for the team');
		expect(readable).toContain('sent automatically with');
	});

	it('sends HTML, CC, BCC and Reply-To recipients', async () => {
		const { mail, message } = await sendOnce({
			emailFormat: 'html',
			options: {
				appendAttribution: false,
				ccEmail: 'cc@example.com',
				bccEmail: 'bcc@example.com',
				replyTo: 'reply@example.com',
			},
			html: '<p>HTML body text</p>',
		});

		const readable = withoutSoftBreaks(mail);
		expect(readable).toContain('<p>HTML body text</p>');
		expect(readable).toContain('cc@example.com');
		expect(readable).toContain('reply@example.com');
		expect(message.recipients).toEqual(
			expect.arrayContaining(['recipient@example.com', 'cc@example.com', 'bcc@example.com']),
		);
	});

	it('sends both message formats', async () => {
		const { mail } = await sendOnce({
			emailFormat: 'both',
			text: 'Plain alternative part',
			html: '<p>HTML alternative part</p>',
		});

		const readable = withoutSoftBreaks(mail);
		expect(readable).toContain('Plain alternative part');
		expect(readable).toContain('<p>HTML alternative part</p>');
	});

	it('delivers a body of a few kilobytes unchanged', async () => {
		const body = '0123456789'.repeat(400);
		const { mail } = await sendOnce({ emailFormat: 'text', text: body });

		expect(decodeTextBody(mail)).toContain(body);
	});

	it('attaches inline and regular binary files', async () => {
		const inlineBytes = 'inline-image-bytes';
		const fileBytes = 'regular-report-bytes';
		const { mail } = await sendOnce(
			{
				options: {
					appendAttribution: false,
					attachments: 'image_1',
					fileAttachments: 'report',
				},
			},
			{
				items: [
					{
						json: {},
						binary: {
							image_1: {
								data: base64Of(inlineBytes),
								mimeType: 'image/png',
								fileName: 'pixel.png',
							},
							report: {
								data: base64Of(fileBytes),
								mimeType: 'application/pdf',
								fileName: 'report.pdf',
							},
						},
					},
				],
			},
		);

		expect(mail).toContain(base64Of(inlineBytes));
		expect(mail).toContain(base64Of(fileBytes));
		expect(mail).toContain('Content-ID: <image_1>');
		expect(mail).toContain('report.pdf');
	});

	it('still verifies an SMTP credential', async () => {
		smtp = await startSmtpServer();
		const result = await smtpConnectionTest.call({} as any, {
			data: { host: smtp.host, port: smtp.port, secure: false },
		} as any);

		expect(result.status).toBe('OK');
	});
});
