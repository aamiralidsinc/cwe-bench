// Cross-site submissions when a site mounts the standalone fragment renderer.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
	buildApp,
	fragmentsHandler,
	honoApp,
	isClientError,
	req,
	urlencoded,
} from '../csrf-fixture.ts';

describe('hono: fragment renderer', () => {
	it('refuses a cross-site urlencoded POST to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['fragments']).fetch(req('/form', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site text/plain PUT to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['fragments']).fetch(
			req('/form', { method: 'PUT', contentType: 'text/plain', body: 'item=1' }),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});
});

describe('astro/fetch: fragment renderer', () => {
	it('refuses a cross-site request without a content type before the page renders', async () => {
		const { app, ran } = buildApp();
		const res = await fragmentsHandler(app, req('/form', { method: 'PATCH', body: 'item=1' }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site form POST whose content type differs in case and has parameters', async () => {
		const { app, ran } = buildApp();
		const res = await fragmentsHandler(
			app,
			req('/form', {
				contentType: 'Application/X-WWW-Form-Urlencoded; charset=UTF-8',
				body: 'item=1',
			}),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});
});
