// Cross-site submissions to pages when a site mounts the fragment dispatcher.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { buildApp, honoApp, isClientError, partialsHandler, req } from '../csrf-fixture.ts';

const multipart = () => ({
	contentType: 'multipart/form-data; boundary=----fixture',
	body: '--fixture--\r\n',
});

describe('hono: fragment dispatcher', () => {
	it('refuses a cross-site multipart POST to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['partials']).fetch(req('/form', multipart()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site text/plain PUT to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['partials']).fetch(
			req('/form', { method: 'PUT', contentType: 'text/plain', body: 'item=1' }),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site form POST whose content type differs in case and has parameters', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['partials']).fetch(
			req('/form', {
				contentType: 'Application/X-WWW-Form-Urlencoded; charset=UTF-8',
				body: 'item=1',
			}),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});
});

describe('astro/fetch: fragment dispatcher', () => {
	it('refuses a cross-site request without a content type before the page renders', async () => {
		const { app, ran } = buildApp();
		const res = await partialsHandler(app, req('/form', { method: 'PATCH', body: 'item=1' }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});
});
