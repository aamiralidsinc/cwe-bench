// Shared fixture for the hidden origin-check tests. Builds an on-demand (server output) App with
// one form action, one JSON action, a page, a form-action target page and an API endpoint. Every
// handler only bumps a counter in `ran`, so a test can tell whether a request reached it.
import { Hono } from 'hono';
import { defineAction } from '../../dist/actions/runtime/server.js';
import { appSymbol } from '../../dist/core/constants.js';
import * as astroHono from '../../dist/core/hono/index.js';
import * as astroFetch from '../../dist/core/fetch/index.js';
import { createComponent, render } from '../../dist/runtime/server/index.js';
import { createEndpoint, createPage, createRouteData, createTestApp } from './mocks.ts';
import { spreadPart, staticPart } from './routing/test-helpers.ts';

export const SITE = 'http://localhost';
export const FOREIGN = 'http://attacker.example';

export type Ran = { action: number; jsonAction: number; endpoint: number; page: number };

export function buildApp(opts: { checkOrigin?: boolean } = {}) {
	const ran: Ran = { action: 0, jsonAction: 0, endpoint: 0, page: 0 };
	const home = createComponent(() => render`<h1>home</h1>`);
	const form = createComponent((result: any, props: any, slots: any) => {
		const Astro = result.createAstro(props, slots);
		if (Astro.request.method !== 'GET' && Astro.request.method !== 'HEAD') ran.page++;
		return render`<h1>form page</h1>`;
	});
	const bump = () => {
		ran.endpoint++;
		return new Response('endpoint-ok');
	};
	const app = createTestApp(
		[
			createPage(home, { route: '/' }),
			createPage(form, { route: '/form' }),
			createEndpoint(
				{ GET: bump, HEAD: bump, OPTIONS: bump, POST: bump, PUT: bump, PATCH: bump, DELETE: bump },
				{ route: "/api/item" },
			),
			{
				routeData: createRouteData({
					route: '/_actions/[...path]',
					type: 'endpoint',
					component: 'astro/actions/runtime/entrypoints/route.js',
					segments: [[staticPart('_actions')], [spreadPart('...path')]],
					pathname: undefined,
				}),
				module: (async () => ({
					page: () => import('../../dist/actions/runtime/entrypoints/route.js'),
				})) as any,
			},
		],
		{
			checkOrigin: opts.checkOrigin ?? true,
			// The site's own middleware (src/middleware.ts): passes every request through.
			middleware: () => ({ onRequest: (_ctx: any, next: any) => next() }),
			actionBodySizeLimit: 1024 * 1024,
			actions: () => ({
				server: {
					addItem: defineAction({
						accept: 'form',
						handler: async () => {
							ran.action++;
							return { added: 1 };
						},
					}),
					addItemJson: defineAction({
						accept: 'json',
						handler: async () => {
							ran.jsonAction++;
							return { added: 1 };
						},
					}),
				},
			}),
		},
	);
	return { app, ran };
}

type AstroApp = ReturnType<typeof buildApp>['app'];

/** A Hono app that attaches the Astro app to each request, then mounts `parts` in order. */
export function honoApp(app: AstroApp, parts: Array<'actions' | 'middleware' | 'pages'>) {
	const hono = new Hono();
	hono.use(async (c, next) => {
		Reflect.set(c.req.raw, appSymbol, app);
		await next();
	});
	for (const p of parts) hono.use((astroHono as any)[p]());
	return hono;
}

/**
 * A plain fetch handler built from the `astro/fetch` primitives: actions first, then page
 * dispatch, with no middleware step.
 */
export async function fetchHandler(app: AstroApp, request: Request): Promise<Response> {
	Reflect.set(request, appSymbol, app);
	const state = new (astroFetch as any).FetchState(request);
	const actionResult = (astroFetch as any).actions(state);
	if (actionResult) {
		const response = await actionResult;
		if (response) return response;
	}
	return (astroFetch as any).pages(state);
}

/** The standard (batteries-included) path, for reference behaviour. */
export function standardRender(app: AstroApp, request: Request): Promise<Response> {
	return app.render(request);
}

export function req(
	path: string,
	init: { method?: string; origin?: string | null; contentType?: string | null; body?: any } = {},
): Request {
	const headers: Record<string, string> = {};
	if (init.origin !== null) headers.origin = init.origin ?? FOREIGN;
	if (init.contentType) headers['content-type'] = init.contentType;
	return new Request(SITE + path, {
		method: init.method ?? 'POST',
		headers,
		body: init.body,
	});
}

export const urlencoded = (origin?: string | null) => ({
	origin,
	contentType: 'application/x-www-form-urlencoded',
	body: 'item=1',
});

export function isClientError(status: number): boolean {
	return status >= 400 && status < 500;
}
