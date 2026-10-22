import type { BaseApp } from '../app/base.js';
import type { FetchState } from '../fetch/fetch-state.js';
import type { Pipeline } from '../base-pipeline.js';
import { renderPage } from '../../runtime/server/index.js';
import { ASTRO_ERROR_HEADER } from '../constants.js';

/**
 * Renders the matched page route on its own, for hosts that patch a part of an
 * already-loaded page in place instead of loading a full document.
 *
 * The helper renders the matched page component itself: it does not resolve or
 * dispatch any other route type, does not read the request again and does not
 * run the pipeline's middleware chain.
 */
export class FragmentHandler {
	#app: BaseApp<Pipeline>;

	constructor(app: BaseApp<Pipeline>) {
		this.#app = app;
	}

	async handle(state: FetchState): Promise<Response> {
		if (!state.routeData || state.routeData.type !== 'page') {
			return new Response(null, { status: 404, headers: { [ASTRO_ERROR_HEADER]: 'true' } });
		}

		state.resetResponseMetadata();
		const componentInstance = await state.loadComponentInstance();
		const props = await state.getProps();
		const actionApiContext = state.getActionAPIContext();
		const result = await state.createResult(componentInstance!, actionApiContext);
		const response = await renderPage(
			result,
			componentInstance?.default as any,
			props,
			state.slots ?? {},
			this.#app.pipeline.streaming,
			state.routeData!,
		);
		state.response = response;
		return response;
	}
}
