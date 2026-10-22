// Legitimate requests that must keep working however the request pipeline is composed.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
	FOREIGN,
	SITE,
	buildApp,
	fetchHandler,
	honoApp,
	isClientError,
	req,
	standardRender,
	urlencoded,
} from '../csrf-fixture.ts';

const ORDER = ['actions', 'middleware', 'pages'] as const;
const ok = (status: number) => status >= 200 && status < 300;

describe('same-site submissions still reach actions, endpoints and pages', () => {
	it('hono actions-first: same-site RPC form action runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, [...ORDER]).fetch(req('/_actions/addItem', urlencoded(SITE)));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.action, 1);
	});

	it('hono actions-first: same-site form action on a page runs and the page renders', async () => {
		const { app, ran } = buildApp();
		const body = new FormData();
		body.set('item', '1');
		const res = await honoApp(app, [...ORDER]).fetch(req('/form?_action=addItem', { origin: SITE, body }));
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
		assert.equal(ran.action, 1);
	});

	it('hono pages() without middleware(): same-site form POST reaches the endpoint', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(req('/api/item', urlencoded(SITE)));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(await res.text(), 'endpoint-ok');
		assert.equal(ran.endpoint, 1);
	});

	it('hono pages() without middleware(): same-site DELETE without content type reaches the endpoint', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(req('/api/item', { method: 'DELETE', origin: SITE }));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.endpoint, 1);
	});

	it('hono pages() without middleware(): same-site form POST renders the page', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(req('/form', urlencoded(SITE)));
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});

	it('astro/fetch primitives: same-site RPC action and endpoint POST run', async () => {
		const { app, ran } = buildApp();
		const a = await fetchHandler(app, req('/_actions/addItem', urlencoded(SITE)));
		assert.ok(ok(a.status), `got ${a.status}`);
		const e = await fetchHandler(app, req('/api/item', { method: 'PUT', origin: SITE }));
		assert.ok(ok(e.status), `got ${e.status}`);
		assert.equal(ran.action, 1);
		assert.equal(ran.endpoint, 1);
	});
});

describe('cross-site requests that are not form-like keep working', () => {
	it('hono actions-first: cross-site JSON RPC action runs', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, [...ORDER]).fetch(
			req('/_actions/addItemJson', { contentType: 'application/json', body: '{}' }),
		);
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.jsonAction, 1);
	});

	it('astro/fetch primitives: cross-site JSON RPC action runs', async () => {
		const { app, ran } = buildApp();
		const res = await fetchHandler(
			app,
			req('/_actions/addItemJson', { contentType: 'application/json', body: '{}' }),
		);
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.jsonAction, 1);
	});

	it('hono pages() without middleware(): cross-site JSON PUT reaches the endpoint', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['pages']).fetch(
			req('/api/item', { method: 'PUT', contentType: 'application/json', body: '{"item":1}' }),
		);
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.endpoint, 1);
	});

	it('hono pages() without middleware(): cross-site GET, HEAD and OPTIONS reach the endpoint', async () => {
		const { app, ran } = buildApp();
		const hono = honoApp(app, ['pages']);
		for (const method of ['GET', 'HEAD', 'OPTIONS']) {
			const res = await hono.fetch(req('/api/item', { method }));
			assert.ok(ok(res.status), `${method}: got ${res.status}`);
		}
		assert.equal(ran.endpoint, 3);
	});

	it('astro/fetch primitives: cross-site GET renders a page', async () => {
		const { app } = buildApp();
		const res = await fetchHandler(app, req('/', { method: 'GET' }));
		assert.equal(res.status, 200);
		assert.match(await res.text(), /home/);
	});
});

describe('origin check disabled in the configuration', () => {
	it('hono actions-first: cross-site form action runs', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await honoApp(app, [...ORDER]).fetch(req('/_actions/addItem', urlencoded()));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.action, 1);
	});

	it('hono pages() without middleware(): cross-site form POST reaches the endpoint', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await honoApp(app, ['pages']).fetch(req('/api/item', urlencoded()));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.endpoint, 1);
	});

	it('astro/fetch primitives: cross-site form action and endpoint DELETE run', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const a = await fetchHandler(app, req('/_actions/addItem', urlencoded()));
		assert.ok(ok(a.status), `got ${a.status}`);
		const e = await fetchHandler(app, req('/api/item', { method: 'DELETE' }));
		assert.ok(ok(e.status), `got ${e.status}`);
		assert.equal(ran.action, 1);
		assert.equal(ran.endpoint, 1);
	});
});

describe('standard request handling keeps its behaviour', () => {
	it('refuses a cross-site form POST to an endpoint and lets a same-site one through', async () => {
		const { app, ran } = buildApp();
		const bad = await standardRender(app, req('/api/item', urlencoded()));
		assert.ok(isClientError(bad.status), `got ${bad.status}`);
		assert.equal(ran.endpoint, 0);
		const good = await standardRender(app, req('/api/item', urlencoded(SITE)));
		assert.ok(ok(good.status), `got ${good.status}`);
		assert.equal(ran.endpoint, 1);
	});

	it('runs a same-site RPC action and a cross-site JSON one, refuses a cross-site form one', async () => {
		const { app, ran } = buildApp();
		const a = await standardRender(app, req('/_actions/addItem', urlencoded(SITE)));
		assert.ok(ok(a.status), `got ${a.status}`);
		const j = await standardRender(
			app,
			req('/_actions/addItemJson', { origin: FOREIGN, contentType: 'application/json', body: '{}' }),
		);
		assert.ok(ok(j.status), `got ${j.status}`);
		const x = await standardRender(app, req('/_actions/addItem', urlencoded()));
		assert.ok(isClientError(x.status), `got ${x.status}`);
		assert.equal(ran.action, 1);
		assert.equal(ran.jsonAction, 1);
	});
});
