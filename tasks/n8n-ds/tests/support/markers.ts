import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

/**
 * A harmless local file whose content is a unique, header-safe marker. If the
 * marker ever shows up in a delivered message the product read the file.
 */
export function makeMarkerFile(label = 'local-file') {
	const dir = mkdtempSync(path.join(tmpdir(), 'n8n-ds-marker-'));
	const content = `n8n-marker-${label}-${Math.random().toString(36).slice(2, 10)}-content`;
	const file = path.join(dir, 'marker.txt');
	writeFileSync(file, `${content}\n`, 'utf8');
	return { file, content };
}

/** Base64 of the marker, for messages that encode file contents as an attachment. */
export function base64Of(value: string): string {
	return Buffer.from(value, 'utf8').toString('base64');
}
