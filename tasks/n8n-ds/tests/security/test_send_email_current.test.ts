import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { makeExecuteContext } from '../support/context';
import { startHttpRecorder, type HttpRecorder } from '../support/http-recorder';
import { makeMarkerFile } from '../support/markers';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const emailSend = new EmailSend();
const currentSend = emailSend.getNodeType(2.1);

let smtp: SmtpServer | undefined;
let recorder: HttpRecorder | undefined;

afterEach(async () => {
	await recorder?.close();
	recorder = undefined;
	await smtp?.close();
	smtp = undefined;
});

async function sendOnce(overrides: Record<string, unknown>) {
	if (smtp) {
		await smtp.close();
		smtp = undefined;
	}
	smtp = await startSmtpServer();
	const params: Record<string, unknown> = {
		operation: 'send',
		fromEmail: 'sender@example.com',
		toEmail: 'recipient@example.com',
		subject: 'Status update',
		emailFormat: 'html',
		options: { appendAttribution: false },
		text: '',
		html: '<p>hello</p>',
		...overrides,
	};
	const context = makeExecuteContext(params, {
		typeVersion: 2.1,
		credentials: { host: smtp.host, port: smtp.port, secure: false },
	});

	let failure: unknown;
	try {
		await currentSend.execute.call(context);
	} catch (error) {
		failure = error;
	}
	return { failure, mail: smtp.allText() };
}

describe('Send Email, current version: message values that name content', () => {
	it('does not put a local file into the HTML body', async () => {
		const marker = makeMarkerFile('html-path');
		const { mail } = await sendOnce({ emailFormat: 'html', html: { path: marker.file } });

		expect(mail).not.toContain(marker.content);
	});

	it('does not put a local file into the plain-text body', async () => {
		const marker = makeMarkerFile('text-path');
		const { mail } = await sendOnce({ emailFormat: 'text', text: { path: marker.file } });

		expect(mail).not.toContain(marker.content);
	});

	it('does not fetch a URL and put the response into the HTML body', async () => {
		const marker = makeMarkerFile('html-href');
		recorder = await startHttpRecorder(marker.content);
		const { mail } = await sendOnce({
			emailFormat: 'html',
			html: { href: `${recorder.baseUrl}/content.txt` },
		});

		expect(recorder.requests).toHaveLength(0);
		expect(mail).not.toContain(marker.content);
	});

	it('does not fetch a URL and put the response into the plain-text body', async () => {
		const marker = makeMarkerFile('text-href');
		recorder = await startHttpRecorder(marker.content);
		const { mail } = await sendOnce({
			emailFormat: 'text',
			text: { href: `${recorder.baseUrl}/content.txt` },
		});

		expect(recorder.requests).toHaveLength(0);
		expect(mail).not.toContain(marker.content);
	});
});

describe('Send Email, current version: message values that are not text', () => {
	it('delivers an array value as text instead of failing', async () => {
		const { failure, mail } = await sendOnce({
			emailFormat: 'text',
			text: ['first line', 'second line'],
		});

		expect(failure).toBeUndefined();
		expect(mail).toContain('first line');
		expect(mail).toContain('second line');
	});

	it('delivers numeric and boolean values as their text form', async () => {
		const numeric = await sendOnce({ emailFormat: 'text', text: 424242 });
		expect(numeric.failure).toBeUndefined();
		expect(numeric.mail).toContain('424242');

		const boolean = await sendOnce({ emailFormat: 'text', text: true });
		expect(boolean.failure).toBeUndefined();
		expect(boolean.mail).toContain('true');
	});
});
