// Cross-site submissions to Astro Actions when the Hono app mounts actions() before middleware().
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { buildApp, honoApp, isClientError, req, urlencoded } from '../csrf-fixture.ts';

const ORDER = ['actions', 'middleware', 'pages'] as const;

describe('hono: actions() mounted before middleware()', () => {
	it('refuses a cross-site urlencoded RPC action call before the action runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, [...ORDER]).fetch(req('/_actions/addItem', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});

	it('refuses a cross-site multipart form action posted to a page before the action runs', async () => {
		const { app, ran } = buildApp();
		const body = new FormData();
		body.set('item', '1');
		const res = await honoApp(app, [...ORDER]).fetch(req('/form?_action=addItem', { body }));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
		assert.equal(ran.page, 0, 'the page must not render');
	});

	it('refuses a form action call that carries no Origin header', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, [...ORDER]).fetch(req('/_actions/addItem', urlencoded(null)));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});

	it('refuses a cross-site call whose form content type differs in case and has parameters', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, [...ORDER]).fetch(
			req('/_actions/addItem', {
				contentType: 'Application/X-WWW-Form-Urlencoded; charset=UTF-8',
				body: 'item=1',
			}),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});

	it('refuses a cross-site action call when the app mounts actions() and pages() only', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['actions', 'pages']).fetch(req('/_actions/addItem', urlencoded()));
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});
});
