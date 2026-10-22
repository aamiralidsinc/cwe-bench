import type { BaseApp } from '../app/base.js';
import type { FetchState } from '../fetch/fetch-state.js';
import type { Pipeline } from '../base-pipeline.js';
import type { RewritePayload } from '../../types/public/common.js';
import { PagesHandler } from '../pages/handler.js';
import { applyRewriteToState } from './handler.js';

/**
 * Resolves a rewrite target and renders the rewritten route.
 *
 * Hosts that keep legacy URLs alive mount this helper before their own
 * routing: it looks the target up in the app's routes, points the state at it
 * and dispatches the route. Routing has already matched the incoming path, so
 * the target is dispatched directly instead of running the middleware chain a
 * second time.
 */
export class RewriteHandler {
	#app: BaseApp<Pipeline>;
	#pages: PagesHandler;

	constructor(app: BaseApp<Pipeline>) {
		this.#app = app;
		this.#pages = new PagesHandler(app.pipeline);
	}

	async handle(state: FetchState, payload: RewritePayload): Promise<Response> {
		const result = await this.#app.pipeline.tryRewrite(payload, state.request);
		applyRewriteToState(state, payload, result, { mergeCookies: true });
		return this.#pages.handle(state, state.getAPIContext());
	}
}
