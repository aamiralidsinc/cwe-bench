// Cross-site submissions to on-demand endpoints and pages when the Hono app mounts pages() without
// middleware().
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { buildApp, honoApp, isClientError, req, urlencoded } from '../csrf-fixture.ts';

describe('hono: pages() without middleware()', () => {
	it('refuses a cross-site text/plain POST to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(
			req('/api/item', { contentType: 'text/plain', body: 'item=1' }),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});

	it('refuses a cross-site DELETE without a content type to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(req('/api/item', { method: 'DELETE' }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});

	it('refuses a cross-site form POST to a page before it renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(req('/form', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.page, 0, 'the page must not render');
	});
});
