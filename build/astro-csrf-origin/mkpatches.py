#!/usr/bin/env python3
"""Regenerate build/astro-csrf-origin/checks/*.patch from the pinned worktree.

    python3 -I mkpatches.py <pinned-worktree>

Each variant starts from the pinned tree (optionally with the reference fix applied), applies
literal text edits, and is written as a `git diff` against the pinned commit.
"""
import subprocess
import sys
from pathlib import Path

WT = Path(sys.argv[1]).resolve()
HERE = Path(__file__).resolve().parent
ORACLE = HERE.parent.parent / "tasks" / "astro-csrf-origin" / "solution" / "fix.patch"
OUT = HERE / "checks"
A = "packages/astro/src/"


def git(*args, check=True):
    return subprocess.run(["git", "-C", str(WT), *args], check=check, capture_output=True, text=True)


def reset():
    git("checkout", "-q", "--", ".")
    git("clean", "-qfd", "--", "packages/astro/src")


def apply_oracle():
    git("apply", str(ORACLE))


def edit(rel, old, new, count=1):
    p = WT / A / rel
    s = p.read_text()
    if s.count(old) != count:
        raise SystemExit(f"{rel}: expected {count} match(es) for {old[:60]!r}, found {s.count(old)}")
    p.write_text(s.replace(old, new))


def save(name):
    git("add", "-A", "--intent-to-add", "packages/astro/src")
    diff = git("diff", "--", "packages/astro/src").stdout
    git("reset", "-q")
    if not diff.strip():
        raise SystemExit(f"{name}: empty diff")
    (OUT / name).write_text(diff)
    print("wrote", name)


ACTION_COMMENT = """		// The origin check normally runs in the origin-check middleware, but the
		// action dispatch can run before that middleware depending on how the
		// pipeline is composed. Apply the same check here so it holds regardless
		// of ordering.
"""
PAGES_COMMENT = """		// The origin check normally runs in the origin-check middleware, but a
		// composable pipeline can dispatch here without running `middleware()`
		// first (or at all). Apply the same check so it holds regardless of how
		// the pipeline is composed.
"""
ORACLE_ACTION_CHECK = """		if (
			state.pipeline.manifest.checkOrigin &&
			isForbiddenCrossOriginRequest(apiContext.request, apiContext.url, apiContext.isPrerendered)
		) {
			return Promise.resolve(createCrossOriginForbiddenResponse(apiContext.request));
		}
"""
ORACLE_PAGES_CHECK = """		if (
			this.#pipeline.manifest.checkOrigin &&
			isForbiddenCrossOriginRequest(ctx.request, ctx.url, ctx.isPrerendered)
		) {
			return createCrossOriginForbiddenResponse(ctx.request);
		}
"""
ACTION_IMPORT = """import {
	createCrossOriginForbiddenResponse,
	isForbiddenCrossOriginRequest,
} from '../core/app/origin-check.js';
"""
PAGES_IMPORT = """import {
	createCrossOriginForbiddenResponse,
	isForbiddenCrossOriginRequest,
} from '../app/origin-check.js';
"""


def oracle_without_dispatch_checks():
    """The reference refactor (shared predicate) with neither dispatch-site check."""
    apply_oracle()
    edit("actions/handler.ts", ACTION_COMMENT + ORACLE_ACTION_CHECK, "")
    edit("actions/handler.ts", ACTION_IMPORT, "")
    edit("core/pages/handler.ts", PAGES_COMMENT + ORACLE_PAGES_CHECK, "")
    edit("core/pages/handler.ts", PAGES_IMPORT, "")


def wrapper_guard(prefix):
    # A guard for a composable wrapper that has a FetchState `state` in scope.
    return f"""	if (state.routeData && state.pipeline.manifest.checkOrigin) {{
		const ctx = state.getAPIContext();
		if (isForbiddenCrossOriginRequest(ctx.request, ctx.url, ctx.isPrerendered)) {{
			return {prefix}createCrossOriginForbiddenResponse(ctx.request);
		}}
	}}
"""


OUT.mkdir(exist_ok=True)

# --- security_fail: lever "lower-level astro/fetch API" -------------------------------------
# Guard only the Hono wrappers (the reported integration); astro/fetch primitives stay open.
reset(); oracle_without_dispatch_checks()
edit("core/hono/index.ts", "\ttrailingSlash as fetchTrailingSlash,\n} from '../fetch/index.js';\n",
     "\ttrailingSlash as fetchTrailingSlash,\n} from '../fetch/index.js';\nimport {\n\tcreateCrossOriginForbiddenResponse,\n"
     "\tisForbiddenCrossOriginRequest,\n} from '../app/origin-check.js';\n")
edit("core/hono/index.ts",
     "\treturn async (context, honoNext) => {\n\t\tconst result = fetchActions(getFetchState(context));",
     "\treturn async (context, honoNext) => {\n\t\tconst state = getFetchState(context);\n"
     + wrapper_guard("").replace("\n\t", "\n\t\t").replace("\tif (state", "\t\tif (state", 1)
     + "\t\tconst result = fetchActions(state);")
edit("core/hono/index.ts",
     "\treturn async (context, _honoNext) => {\n\t\treturn fetchPages(getFetchState(context));",
     "\treturn async (context, _honoNext) => {\n\t\tconst state = getFetchState(context);\n"
     + wrapper_guard("").replace("\n\t", "\n\t\t").replace("\tif (state", "\t\tif (state", 1)
     + "\t\treturn fetchPages(state);")
save("sf_hono_wrappers_only.patch")

# --- security_fail: lever "page/endpoint dispatch without the middleware step" --------------
# Guard only the action dispatch (the advisory's example); page/endpoint dispatch stays open.
reset(); apply_oracle()
edit("core/pages/handler.ts", PAGES_COMMENT + ORACLE_PAGES_CHECK, "")
edit("core/pages/handler.ts", PAGES_IMPORT, "")
save("sf_actions_only.patch")

# --- security_fail: form actions on page routes left open (RPC only) ------------------------
reset(); apply_oracle()
edit("actions/handler.ts", "\t\t\tstate.pipeline.manifest.checkOrigin &&\n",
     "\t\t\tstate.pipeline.manifest.checkOrigin &&\n\t\t\taction.calledFrom === 'rpc' &&\n")
save("sf_rpc_actions_only.patch")

# --- security_fail: only POST is checked ----------------------------------------------------
reset(); apply_oracle()
edit("core/app/origin-check.ts",
     "\tif (SAFE_METHODS.includes(request.method)) {\n\t\treturn false;\n\t}\n\tconst isSameOrigin",
     "\tif (SAFE_METHODS.includes(request.method)) {\n\t\treturn false;\n\t}\n"
     "\tif (request.method !== 'POST') {\n\t\treturn false;\n\t}\n\tconst isSameOrigin")
save("sf_post_only.patch")

# --- security_fail: exact content-type match (case / parameters slip through) ----------------
reset(); apply_oracle()
edit("core/app/origin-check.ts",
     "\t\tconst formLikeHeader = hasFormLikeHeader(request.headers.get('content-type'));",
     "\t\tconst formLikeHeader = FORM_CONTENT_TYPES.includes(request.headers.get('content-type') ?? '');")
save("sf_exact_content_type.patch")

# --- security_fail: a request without an Origin header is treated as same-site ---------------
reset(); apply_oracle()
edit("core/app/origin-check.ts",
     "\tconst isSameOrigin = request.headers.get('origin') === url.origin;",
     "\tconst origin = request.headers.get('origin');\n\tif (!origin) {\n\t\treturn false;\n\t}\n"
     "\tconst isSameOrigin = origin === url.origin;")
save("sf_absent_origin_allowed.patch")

# --- security_fail: refusal by throwing (500) instead of a client error ----------------------
reset(); apply_oracle()
edit("actions/handler.ts",
     "\t\t\treturn Promise.resolve(createCrossOriginForbiddenResponse(apiContext.request));",
     "\t\t\tthrow new Error('Cross-site form submissions are forbidden');")
edit("core/pages/handler.ts",
     "\t\t\treturn createCrossOriginForbiddenResponse(ctx.request);",
     "\t\t\tthrow new Error('Cross-site form submissions are forbidden');")
save("sf_throw_instead_of_refusal.patch")

# --- security_fail: action check runs after the action has executed -------------------------
reset(); apply_oracle()
edit("actions/handler.ts", ACTION_COMMENT + ORACLE_ACTION_CHECK, "")
edit("actions/handler.ts", "\t\treturn this.#executeAction(action, setActionResult);",
     "\t\tconst forbidden =\n\t\t\tstate.pipeline.manifest.checkOrigin &&\n"
     "\t\t\tisForbiddenCrossOriginRequest(apiContext.request, apiContext.url, apiContext.isPrerendered);\n"
     "\t\treturn this.#executeAction(action, setActionResult).then((response) =>\n"
     "\t\t\tforbidden ? createCrossOriginForbiddenResponse(apiContext.request) : response,\n\t\t);")
save("sf_check_after_action.patch")

# --- functional_fail: refuse every cross-site request on the dispatch paths ------------------
reset(); apply_oracle()
edit("actions/handler.ts",
     "\t\t\tisForbiddenCrossOriginRequest(apiContext.request, apiContext.url, apiContext.isPrerendered)",
     "\t\t\tapiContext.request.headers.get('origin') !== apiContext.url.origin")
edit("core/pages/handler.ts",
     "\t\t\tisForbiddenCrossOriginRequest(ctx.request, ctx.url, ctx.isPrerendered)",
     "\t\t\tctx.request.headers.get('origin') !== ctx.url.origin")
save("ff_refuse_all_cross_site.patch")

# --- functional_fail: ignores the security.checkOrigin setting ------------------------------
reset(); apply_oracle()
edit("actions/handler.ts", "\t\t\tstate.pipeline.manifest.checkOrigin &&\n", "")
edit("core/pages/handler.ts", "\t\t\tthis.#pipeline.manifest.checkOrigin &&\n", "")
save("ff_ignores_check_origin_setting.patch")

# --- functional_fail: shared helper widened so JSON counts as form-like ----------------------
reset(); apply_oracle()
edit("core/app/origin-check.ts", "\t'text/plain',\n];", "\t'text/plain',\n\t'application/json',\n];")
save("ff_json_counted_as_form.patch")

# --- pass (hardening): reference fix plus the same guard in the shared dispatch and wrappers -
reset(); apply_oracle()
edit("core/pages/handler.ts",
     "\tasync handle(state: FetchState, ctx: APIContext): Promise<Response> {\n"
     "\t\tconst pipeline = this.#pipeline;\n",
     "\tasync handle(state: FetchState, ctx: APIContext): Promise<Response> {\n"
     "\t\tconst pipeline = this.#pipeline;\n"
     "\t\tif (\n\t\t\tpipeline.manifest.checkOrigin &&\n\t\t\tstate.routeData?.type !== 'redirect' &&\n"
     "\t\t\tisForbiddenCrossOriginRequest(ctx.request, ctx.url, ctx.isPrerendered)\n\t\t) {\n"
     "\t\t\treturn createCrossOriginForbiddenResponse(ctx.request);\n\t\t}\n")
edit("core/fetch/index.ts", "import { ActionHandler } from '../../actions/handler.js';\n",
     "import { ActionHandler } from '../../actions/handler.js';\nimport {\n"
     "\tcreateCrossOriginForbiddenResponse,\n\tisForbiddenCrossOriginRequest,\n} from '../app/origin-check.js';\n")
edit("core/fetch/index.ts",
     "\t\tactionHandlers.set(app, handler);\n\t}\n",
     "\t\tactionHandlers.set(app, handler);\n\t}\n"
     + wrapper_guard("Promise.resolve(").replace("(ctx.request);", "(ctx.request));"))
save("pass_hardening.patch")

# --- pass (alternative): guard the astro/fetch primitives that every composition goes through
reset(); oracle_without_dispatch_checks()
edit("core/fetch/index.ts", "import { ActionHandler } from '../../actions/handler.js';\n",
     "import { ActionHandler } from '../../actions/handler.js';\nimport {\n"
     "\tcreateCrossOriginForbiddenResponse,\n\tisForbiddenCrossOriginRequest,\n} from '../app/origin-check.js';\n")
edit("core/fetch/index.ts",
     "\t\tpagesHandlers.set(app, handler);\n\t}\n",
     "\t\tpagesHandlers.set(app, handler);\n\t}\n"
     + wrapper_guard("Promise.resolve(").replace("(ctx.request);", "(ctx.request));"))
edit("core/fetch/index.ts",
     "\t\tactionHandlers.set(app, handler);\n\t}\n",
     "\t\tactionHandlers.set(app, handler);\n\t}\n"
     + wrapper_guard("Promise.resolve(").replace("(ctx.request);", "(ctx.request));"))
save("pass_alt_fetch_primitives.patch")

reset()
