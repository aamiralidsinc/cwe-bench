/**
 * Decode the top-level body of a captured single-part message, for assertions
 * on what a recipient would actually read. Handles base64 and quoted-printable,
 * the encodings the mail library picks for text parts.
 */
export function decodeTextBody(raw: string): string {
	const separator = raw.includes('\r\n\r\n') ? '\r\n\r\n' : '\n\n';
	const split = raw.indexOf(separator);
	if (split < 0) return raw;
	const headers = raw.slice(0, split);
	const body = raw.slice(split + separator.length);
	const encoding = /content-transfer-encoding:\s*(\S+)/i.exec(headers)?.[1]?.toLowerCase();

	if (encoding === 'base64') {
		return Buffer.from(body.replace(/\s+/g, ''), 'base64').toString('utf8');
	}

	const unsoftwrapped = body.replace(/=\r?\n/g, '');
	return unsoftwrapped.replace(/=([0-9A-Fa-f]{2})/g, (_match, hex: string) =>
		String.fromCharCode(parseInt(hex, 16)),
	);
}
