// Cross-site submissions to API endpoints when a site mounts the endpoint-only dispatcher.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
	buildApp,
	endpointsHandler,
	honoApp,
	isClientError,
	req,
	urlencoded,
} from '../csrf-fixture.ts';

describe('hono: endpoint dispatcher', () => {
	it('refuses a cross-site PUT without a content type to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['endpoints']).fetch(req('/api/item', { method: 'PUT' }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});

	it('refuses a cross-site text/plain POST to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['endpoints']).fetch(
			req('/api/item', { contentType: 'text/plain', body: 'item=1' }),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});
});

describe('astro/fetch: endpoint dispatcher', () => {
	it('refuses a cross-site urlencoded POST to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await endpointsHandler(app, req('/api/item', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});
});
