// Cross-site submissions when a site mounts the rewrite helper that keeps a legacy URL alive.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
	buildApp,
	honoRewrite,
	isClientError,
	req,
	rewriteHandler,
	urlencoded,
} from '../csrf-fixture.ts';

describe('hono: rewrite helper', () => {
	it('refuses a cross-site urlencoded POST rewritten to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoRewrite(app, '/form', req('/legacy', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site multipart POST rewritten to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const body = new FormData();
		body.set('item', '1');
		const res = await honoRewrite(app, '/form', req('/legacy', { body }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site DELETE without a content type rewritten to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoRewrite(app, '/api/item', req('/legacy', { method: 'DELETE' }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});
});

describe('astro/fetch: rewrite helper', () => {
	it('refuses a form submission that carries no Origin header', async () => {
		const { app, ran } = buildApp();
		const res = await rewriteHandler(app, req('/legacy', urlencoded(null)), '/form');
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a cross-site text/plain POST rewritten to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await rewriteHandler(
			app,
			req('/legacy', { contentType: 'text/plain', body: 'item=1' }),
			'/form',
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});
});
