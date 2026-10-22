// Cross-site submissions through a fetch handler built from the astro/fetch primitives
// (actions, then page dispatch; no middleware step).
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { buildApp, fetchHandler, isClientError, req, urlencoded } from '../csrf-fixture.ts';

describe('astro/fetch: actions(state) then pages(state)', () => {
	it('refuses a cross-site urlencoded RPC action call before the action runs', async () => {
		const { app, ran } = buildApp();
		const res = await fetchHandler(app, req('/_actions/addItem', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});

	it('refuses a cross-site PUT without a content type to an endpoint before it runs', async () => {
		const { app, ran } = buildApp();
		const res = await fetchHandler(app, req('/api/item', { method: 'PUT' }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.endpoint, 0, 'the endpoint must not run');
	});
});
