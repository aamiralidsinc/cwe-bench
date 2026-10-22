// Legitimate requests through the endpoint, form-action and fragment dispatchers.
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
	SITE,
	buildApp,
	endpointsHandler,
	formActionsThenPages,
	fragmentsHandler,
	honoApp,
	honoRewrite,
	partialsHandler,
	req,
	rewriteHandler,
	urlencoded,
} from '../csrf-fixture.ts';

const ok = (status: number) => status >= 200 && status < 300;

describe('endpoint dispatcher: legitimate requests', () => {
	it('same-site form POST reaches the endpoint', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['endpoints']).fetch(req('/api/item', urlencoded(SITE)));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(await res.text(), 'endpoint-ok');
		assert.equal(ran.endpoint, 1);
	});

	it('cross-site JSON PUT reaches the endpoint', async () => {
		const { app, ran } = buildApp();
		const res = await endpointsHandler(
			app,
			req('/api/item', { method: 'PUT', contentType: 'application/json', body: '{"item":1}' }),
		);
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.endpoint, 1);
	});

	it('cross-site GET, HEAD and OPTIONS reach the endpoint', async () => {
		const { app, ran } = buildApp();
		for (const method of ['GET', 'HEAD', 'OPTIONS']) {
			const res = await endpointsHandler(app, req('/api/item', { method }));
			assert.ok(ok(res.status), `${method}: got ${res.status}`);
		}
		assert.equal(ran.endpoint, 3);
	});

	it('with the origin check disabled, a cross-site form POST reaches the endpoint', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await honoApp(app, ['endpoints']).fetch(req('/api/item', urlencoded()));
		assert.ok(ok(res.status), `got ${res.status}`);
		assert.equal(ran.endpoint, 1);
	});
});

describe('form-action step: legitimate requests', () => {
	it('same-site form action runs and the page renders', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['formActions', 'pages']).fetch(
			req('/form?_action=addItem', urlencoded(SITE)),
		);
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
		assert.equal(ran.action, 1);
	});

	it('with the origin check disabled, a cross-site form action runs', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await formActionsThenPages(app, req('/form?_action=addItem', urlencoded()));
		assert.equal(res.status, 200);
		assert.equal(ran.action, 1);
	});

	it('non-action requests pass through to the page', async () => {
		const { app, ran } = buildApp();
		const res = await formActionsThenPages(app, req('/form', urlencoded(SITE)));
		assert.equal(res.status, 200);
		assert.equal(ran.action, 0);
		assert.equal(ran.page, 1);
	});
});

describe('fragment dispatcher: legitimate requests', () => {
	it('same-site multipart POST renders the page', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['partials']).fetch(
			req('/form', { origin: SITE, contentType: 'multipart/form-data; boundary=----fixture', body: '--fixture--\r\n' }),
		);
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});

	it('cross-site JSON POST renders the page', async () => {
		const { app, ran } = buildApp();
		const res = await partialsHandler(
			app,
			req('/form', { contentType: 'application/json', body: '{}' }),
		);
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});

	it('cross-site GET renders the page', async () => {
		const { app } = buildApp();
		const res = await partialsHandler(app, req('/form', { method: 'GET' }));
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
	});

	it('with the origin check disabled, a cross-site text/plain PUT renders the page', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await honoApp(app, ['partials']).fetch(
			req('/form', { method: 'PUT', contentType: 'text/plain', body: 'item=1' }),
		);
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});
});

describe('rewrite helper: legitimate requests', () => {
	it('same-site urlencoded POST renders the rewritten page', async () => {
		const { app, ran } = buildApp();
		const res = await honoRewrite(app, '/form', req('/legacy', urlencoded(SITE)));
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
		assert.equal(ran.page, 1);
	});

	it('cross-site JSON POST renders the rewritten page', async () => {
		const { app, ran } = buildApp();
		const res = await rewriteHandler(
			app,
			req('/legacy', { contentType: 'application/json', body: '{"item":1}' }),
			'/form',
		);
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});

	it('cross-site GET renders the rewritten page', async () => {
		const { app } = buildApp();
		const res = await rewriteHandler(app, req('/legacy', { method: 'GET', origin: null }), '/form');
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
	});

	it('same-site form POST reaches the endpoint it rewrites to', async () => {
		const { app, ran } = buildApp();
		const res = await rewriteHandler(
			app,
			req('/legacy', urlencoded(SITE)),
			'/api/item',
		);
		assert.equal(res.status, 200);
		assert.equal(await res.text(), 'endpoint-ok');
		assert.equal(ran.endpoint, 1);
	});

	it('with the origin check disabled, a cross-site form POST renders the rewritten page', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await rewriteHandler(app, req('/legacy', urlencoded()), '/form');
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});
});

describe('fragment renderer: legitimate requests', () => {
	it('same-site form POST renders the page', async () => {
		const { app, ran } = buildApp();
		const res = await honoApp(app, ['fragments']).fetch(req('/form', urlencoded(SITE)));
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
		assert.equal(ran.page, 1);
	});

	it('cross-site JSON POST renders the page', async () => {
		const { app, ran } = buildApp();
		const res = await fragmentsHandler(
			app,
			req('/form', { contentType: 'application/json', body: '{}' }),
		);
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});

	it('cross-site GET renders the page', async () => {
		const { app } = buildApp();
		const res = await fragmentsHandler(app, req('/form', { method: 'GET', origin: null }));
		assert.equal(res.status, 200);
		assert.match(await res.text(), /form page/);
	});

	it('with the origin check disabled, a cross-site form POST renders the page', async () => {
		const { app, ran } = buildApp({ checkOrigin: false });
		const res = await fragmentsHandler(app, req('/form', urlencoded()));
		assert.equal(res.status, 200);
		assert.equal(ran.page, 1);
	});
});
