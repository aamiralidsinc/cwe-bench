import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { makeExecuteContext } from '../support/context';
import { startHttpRecorder, type HttpRecorder } from '../support/http-recorder';
import { makeMarkerFile } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const legacySend = new EmailSend().getNodeType(1);

let smtp: SmtpServer | undefined;
let recorder: HttpRecorder | undefined;

afterEach(async () => {
	await recorder?.close();
	recorder = undefined;
	await smtp?.close();
	smtp = undefined;
});

async function sendLegacyOnce(overrides: Record<string, unknown>) {
	if (smtp) {
		await smtp.close();
		smtp = undefined;
	}
	smtp = await startSmtpServer();
	const params: Record<string, unknown> = {
		fromEmail: 'sender@example.com',
		toEmail: 'recipient@example.com',
		ccEmail: '',
		bccEmail: '',
		subject: 'Legacy status',
		text: 'plain body',
		html: '<p>html body</p>',
		attachments: '',
		options: {},
		...overrides,
	};
	const context = makeExecuteContext(params, {
		typeVersion: 1,
		credentials: { host: smtp.host, port: smtp.port, secure: false },
	});

	let failure: unknown;
	try {
		await legacySend.execute.call(context);
	} catch (error) {
		failure = error;
	}
	return { failure, mail: smtp.allText() };
}

describe('Send Email, first implementation: message values that name content', () => {
	it('does not put a local file into the plain-text body', async () => {
		const marker = makeMarkerFile('legacy-text');
		const { mail } = await sendLegacyOnce({ text: { path: marker.file } });

		expect(mail).not.toContain(marker.content);
	});

	it('does not put a local file into the HTML body', async () => {
		const marker = makeMarkerFile('legacy-html');
		const { mail } = await sendLegacyOnce({ html: { path: marker.file } });

		expect(mail).not.toContain(marker.content);
	});

	it('does not fetch a URL for the HTML body', async () => {
		const marker = makeMarkerFile('legacy-href');
		recorder = await startHttpRecorder(marker.content);
		const { mail } = await sendLegacyOnce({ html: { href: `${recorder.baseUrl}/body.txt` } });

		expect(recorder.requests).toHaveLength(0);
		expect(mail).not.toContain(marker.content);
	});

	it('delivers a non-text value as text instead of failing', async () => {
		const { failure, mail } = await sendLegacyOnce({ text: ['legacy', 'lines'] });

		expect(failure).toBeUndefined();
		expect(mail).toContain('legacy');
		expect(mail).toContain('lines');
	});
});
