import { SEND_AND_WAIT_OPERATION } from 'n8n-workflow';
import { afterEach, describe, expect, it } from 'vitest';

import { EmailSend } from '../../../nodes/EmailSend/EmailSend.node';
import { makeExecuteContext } from '../support/context';
import { startSmtpServer, type SmtpServer } from '../support/smtp';

const sendAndWaitNode = new EmailSend().getNodeType(2.1);

let smtp: SmtpServer | undefined;

afterEach(async () => {
	await smtp?.close();
	smtp = undefined;
});

function withoutSoftBreaks(text: string) {
	return text.replace(/=\r\n/g, '').replace(/=\n/g, '');
}

async function waitSendOnce(options: Record<string, unknown>) {
	if (smtp) {
		await smtp.close();
		smtp = undefined;
	}
	smtp = await startSmtpServer();
	let waited = false;
	const context = makeExecuteContext(
		{
			operation: SEND_AND_WAIT_OPERATION,
			fromEmail: 'sender@example.com',
			toEmail: 'recipient@example.com',
			message: 'Please approve this request',
			subject: 'Approval needed',
			'approvalOptions.values': { approvalType: 'single' },
			options,
			responseType: 'approval',
			'options.limitWaitTime.values': {},
		},
		{
			typeVersion: 2.1,
			credentials: { host: smtp.host, port: smtp.port, secure: false },
		},
	);
	(context as any).putExecutionToWait = async () => {
		waited = true;
	};

	await sendAndWaitNode.execute.call(context);
	return { mail: smtp.allText(), waited };
}

describe('Send Email, wait-for-response operation: legitimate use', () => {
	it('sends the approval message and waits for the response', async () => {
		const { mail, waited } = await waitSendOnce({ appendAttribution: false });

		const readable = withoutSoftBreaks(mail);
		expect(readable).toContain('Please approve this request');
		expect(readable).toContain('Approval needed');
		expect(waited).toBe(true);
	});

	it('sends a plain-text alternative when one is configured', async () => {
		const { mail } = await waitSendOnce({
			appendAttribution: false,
			plainText: 'Plain alternative body',
		});

		const readable = withoutSoftBreaks(mail);
		expect(readable).toContain('Plain alternative body');
		expect(readable).toContain('Please approve this request');
	});
});
