import re, sys
p = '/app/packages/astro/src/core/fetch/index.ts'
s = open(p).read()

s = s.replace(
"import { PagesHandler } from '../pages/handler.js';\n",
"import { PagesHandler } from '../pages/handler.js';\nimport { FragmentHandler } from '../pages/fragment-handler.js';\n", 1)
s = s.replace(
"import { TrailingSlashHandler } from '../routing/trailing-slash-handler.js';\n",
"import { TrailingSlashHandler } from '../routing/trailing-slash-handler.js';\nimport { RewriteHandler } from '../rewrites/rewrite-handler.js';\n", 1)

anchor = """/**
 * Registers the session provider on the state."""
assert anchor in s
add = """const fragmentHandlers = new WeakMap<BaseApp<Pipeline>, FragmentHandler>();

/**
 * Renders the matched page route as a standalone fragment, for hosts that
 * patch part of a page in place. Page routes only; endpoint routes and
 * unknown paths return a 404.
 */
export function fragments(state: FetchState): Promise<Response> {
\tconst app = getApp(state.request);
\tlet handler = fragmentHandlers.get(app);
\tif (!handler) {
\t\thandler = new FragmentHandler(app);
\t\tfragmentHandlers.set(app, handler);
\t}
\treturn handler.handle(state);
}

const rewriteHandlers = new WeakMap<BaseApp<Pipeline>, RewriteHandler>();

/**
 * Resolves the rewrite target against the app's routes and renders the
 * rewritten route. Use this in a host that keeps legacy URLs alive and
 * dispatches them itself.
 */
export function rewrite(state: FetchState, payload: RewritePayload): Promise<Response> {
\tconst app = getApp(state.request);
\tlet handler = rewriteHandlers.get(app);
\tif (!handler) {
\t\thandler = new RewriteHandler(app);
\t\trewriteHandlers.set(app, handler);
\t}
\treturn handler.handle(state, payload);
}

"""
s = s.replace(anchor, add + anchor, 1)

# RewritePayload type import
s = s.replace(
"import type { Pipeline } from '../base-pipeline.js';\n",
"import type { Pipeline } from '../base-pipeline.js';\nimport type { RewritePayload } from '../../types/public/common.js';\n", 1)
open(p, 'w').write(s)

p = '/app/packages/astro/src/core/hono/index.ts'
s = open(p).read()
s = s.replace("\tredirects as fetchRedirects,\n",
              "\tredirects as fetchRedirects,\n\tfragments as fetchFragments,\n\trewrite as fetchRewrite,\n", 1)
s = s.replace("export { FetchState };\n",
              "import type { RewritePayload } from '../../types/public/common.js';\n\nexport { FetchState };\n", 1)

anchor = """export function sessions(): HonoMiddlewareHandler {"""
add = """export function fragments(): HonoMiddlewareHandler {
\treturn async (context, _honoNext) => {
\t\treturn fetchFragments(getFetchState(context));
\t};
}

export function rewrite(payload: RewritePayload): HonoMiddlewareHandler {
\treturn async (context, _honoNext) => {
\t\treturn fetchRewrite(getFetchState(context), payload);
\t};
}

"""
assert anchor in s
s = s.replace(anchor, add + anchor, 1)
open(p, 'w').write(s)
print("ok")
