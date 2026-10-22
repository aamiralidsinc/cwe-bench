import net from 'node:net';

export type CapturedMail = { raw: string; recipients: string[] };

/**
 * A loopback SMTP server that accepts one or more messages and captures the
 * DATA payload verbatim. Enough of RFC 5321 for the mail library used by the
 * product; it never touches the network.
 */
export async function startSmtpServer() {
	const messages: CapturedMail[] = [];
	const server = net.createServer((socket) => {
		let buffer = '';
		let inData = false;
		const dataLines: string[] = [];
		const recipients: string[] = [];
		socket.write('220 test.local ESMTP\r\n');
		socket.on('data', (chunk) => {
			buffer += chunk.toString('utf8');
			let newline = buffer.indexOf('\r\n');
			while (newline >= 0) {
				const line = buffer.slice(0, newline);
				buffer = buffer.slice(newline + 2);
				newline = buffer.indexOf('\r\n');

				if (inData) {
					if (line === '.') {
						inData = false;
						messages.push({ raw: dataLines.join('\r\n'), recipients: [...recipients] });
						dataLines.length = 0;
						recipients.length = 0;
						socket.write('250 OK\r\n');
					} else {
						dataLines.push(line.startsWith('..') ? line.slice(1) : line);
					}
					continue;
				}

				const verb = line.slice(0, 4).toUpperCase();
				if (verb === 'EHLO') {
					socket.write('250-test.local\r\n250 8BITMIME\r\n');
				} else if (verb === 'DATA') {
					inData = true;
					socket.write('354 End data with <CR><LF>.<CR><LF>\r\n');
				} else if (verb === 'RCPT') {
					const match = /<([^>]*)>/.exec(line);
					if (match) recipients.push(match[1]);
					socket.write('250 OK\r\n');
				} else if (verb === 'QUIT') {
					socket.write('221 Bye\r\n');
					socket.end();
				} else {
					socket.write('250 OK\r\n');
				}
			}
		});
		socket.on('error', () => {});
	});

	await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
	const address = server.address();
	if (!address || typeof address === 'string') throw new Error('no smtp port');

	const close = async () => {
		await new Promise<void>((resolve) => server.close(() => resolve()));
	};

	return {
		host: '127.0.0.1',
		port: address.port,
		messages,
		close,
		/** All captured message payloads, joined, for simple containment checks. */
		allText: () => messages.map((m) => m.raw).join('\n'),
	};
}

export type SmtpServer = Awaited<ReturnType<typeof startSmtpServer>>;
