// Cross-site form actions when a site runs the form-action step itself before rendering pages.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
	buildApp,
	formActionsThenPages,
	honoApp,
	isClientError,
	req,
	urlencoded,
} from '../csrf-fixture.ts';

const multipartBody = () => {
	const body = new FormData();
	body.set('item', '1');
	return body;
};

describe('hono: form-action step', () => {
	it('refuses a cross-site urlencoded form action before the action runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['formActions', 'pages']).fetch(
			req('/form?_action=addItem', urlencoded()),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});

	it('refuses a cross-site multipart form action before the action runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['formActions', 'pages']).fetch(
			req('/form?_action=addItem', { body: multipartBody() }),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});
});

describe('astro/fetch: form-action step', () => {
	it('refuses a form action call that carries no Origin header', async () => {
		const { app, ran } = buildApp();
		const res = await formActionsThenPages(
			app,
			req('/form?_action=addItem', urlencoded(null)),
		);
		assert.ok(isClientError(res.status), `expected a client error, got ${res.status}`);
		assert.equal(ran.action, 0, 'the action must not run');
	});
});
