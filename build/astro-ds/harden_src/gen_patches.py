import os, shutil, subprocess, sys, textwrap

B = "/tmp/b"
SRC = "/tmp/src"          # unguarded + fixed module files
OUT = "/tmp/out"
OLD_FIX = "/tmp/fix.patch"
OLD_CHECKS = "/tmp/checks"

def sh(cmd, cwd=B, check=True):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r

def apply_src(root):
    p = f"{root}/packages/astro/src/core/fetch/index.ts"
    s = open(p).read()
    s = s.replace(
        "import { PagesHandler } from '../pages/handler.js';\n",
        "import { PagesHandler } from '../pages/handler.js';\nimport { FragmentHandler } from '../pages/fragment-handler.js';\n", 1)
    s = s.replace(
        "import { TrailingSlashHandler } from '../routing/trailing-slash-handler.js';\n",
        "import { TrailingSlashHandler } from '../routing/trailing-slash-handler.js';\nimport { RewriteHandler } from '../rewrites/rewrite-handler.js';\n", 1)
    s = s.replace(
        "import type { Pipeline } from '../base-pipeline.js';\n",
        "import type { Pipeline } from '../base-pipeline.js';\nimport type { RewritePayload } from '../../types/public/common.js';\n", 1)
    anchor = "/**\n * Registers the session provider on the state."
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
    open(p, "w").write(s)

    p = f"{root}/packages/astro/src/core/hono/index.ts"
    s = open(p).read()
    s = s.replace("\tredirects as fetchRedirects,\n",
                  "\tredirects as fetchRedirects,\n\tfragments as fetchFragments,\n\trewrite as fetchRewrite,\n", 1)
    s = s.replace("export { FetchState };\n",
                  "import type { RewritePayload } from '../../types/public/common.js';\n\nexport { FetchState };\n", 1)
    anchor = "export function sessions(): HonoMiddlewareHandler {"
    assert anchor in s
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
    s = s.replace(anchor, add + anchor, 1)
    open(p, "w").write(s)

FRAG = "packages/astro/src/core/pages/fragment-handler.ts"
RWT = "packages/astro/src/core/rewrites/rewrite-handler.ts"

def copy(name, dest):
    shutil.copyfile(f"{SRC}/{name}", f"{B}/{dest}")

def patch_alt_fetch():
    """pass_alt_fetch_primitives: guard the astro/fetch wrappers."""
    p = f"{B}/packages/astro/src/core/fetch/index.ts"
    s = open(p).read()
    s = s.replace(
        "export function fragments(state: FetchState): Promise<Response> {\n",
        "export function fragments(state: FetchState): Promise<Response> {\n\tconst refusal = crossOriginRefusal(state);\n\tif (refusal) return Promise.resolve(refusal);\n", 1)
    s = s.replace(
        "export function rewrite(state: FetchState, payload: RewritePayload): Promise<Response> {\n",
        "export function rewrite(state: FetchState, payload: RewritePayload): Promise<Response> {\n\tconst refusal = crossOriginRefusal(state);\n\tif (refusal) return Promise.resolve(refusal);\n", 1)
    open(p, "w").write(s)

def patch_blind():
    """blind: call the FetchState helper in both new modules."""
    p = f"{B}/{FRAG}"
    s = open(p).read()
    s = s.replace(
"\t\tstate.resetResponseMetadata();\n\t\tconst componentInstance",
"\t\tconst originRefusal = state.getOriginCheckRefusal();\n\t\tif (originRefusal) {\n\t\t\treturn originRefusal;\n\t\t}\n\n\t\tstate.resetResponseMetadata();\n\t\tconst componentInstance", 1)
    assert "originRefusal" in s
    open(p, "w").write(s)
    p = f"{B}/{RWT}"
    s = open(p).read()
    s = s.replace(
"\tasync handle(state: FetchState, payload: RewritePayload): Promise<Response> {\n\t\tconst result",
"\tasync handle(state: FetchState, payload: RewritePayload): Promise<Response> {\n\t\tconst originRefusal = state.getOriginCheckRefusal();\n\t\tif (originRefusal) {\n\t\t\treturn originRefusal;\n\t\t}\n\t\tconst result", 1)
    assert "originRefusal" in s
    open(p, "w").write(s)

def reset():
    sh("git reset -q --hard HEAD && git clean -qfd")

def commit_base():
    shutil.rmtree(B, ignore_errors=True)
    os.makedirs(B)
    sh("git -C /app archive HEAD | tar -x -C /tmp/b")
    sh("git init -q -b main && git add -A && git -c user.email=a@b -c user.name=a commit -qm pinned")
    sh("patch -p1 -s < /tmp/injection.patch")
    copy("fragment-handler.plain.ts", FRAG)
    copy("rewrite-handler.plain.ts", RWT)
    apply_src(B)
    sh("git add -A && git -c user.email=a@b -c user.name=a commit -qm injected")
    sh("git diff HEAD~1 HEAD > /tmp/injection_new.patch")
    sh("git tag inj")

def make(name, old_patch, edits):
    reset()
    if old_patch:
        r = sh(f"patch -p1 < {OLD_CHECKS}/{old_patch}", check=False)
        if r.returncode != 0:
            sys.exit(f"apply {old_patch} failed:\n{r.stdout}\n{r.stderr}")
    for fn in edits:
        fn()
    sh("git add -A")
    sh(f"git diff inj > {OUT}/{name}")
    print(name, len(open(f"{OUT}/{name}").read().splitlines()))

os.makedirs(OUT, exist_ok=True)
commit_base()

def fix_old():
    r = sh(f"patch -p1 < {OLD_FIX}", check=False)
    if r.returncode != 0:
        sys.exit(f"apply fix.patch failed:\n{r.stdout}\n{r.stderr}")

# The oracle fix is the old fix.patch + the two guards.
reset()
fix_old()
copy("fragment-handler.fixed.ts", FRAG)
copy("rewrite-handler.fixed.ts", RWT)
sh("git add -A")
sh(f"git diff inj > {OUT}/fix_new.patch")
print("fix_new.patch", len(open(f"{OUT}/fix_new.patch").read().splitlines()))

reset(); fix_old(); copy("rewrite-handler.fixed.ts", RWT); sh("git add -A")
sh(f"git diff inj > {OUT}/sf_miss_fragments.patch")
print("sf_miss_fragments.patch")

reset(); fix_old(); copy("fragment-handler.fixed.ts", FRAG); sh("git add -A")
sh(f"git diff inj > {OUT}/sf_miss_rewrites.patch")
print("sf_miss_rewrites.patch")

# pass_hardening: its shared PagesHandler.handle check covers the rewrite helper.
reset()
r = sh(f"patch -p1 < {OLD_CHECKS}/pass_hardening.patch", check=False)
assert r.returncode == 0, r.stdout + r.stderr
copy("fragment-handler.fixed.ts", FRAG)
sh("git add -A")
sh(f"git diff inj > {OUT}/pass_hardening_new.patch")
print("pass_hardening_new.patch")

# pass_alt_fetch_primitives: guard the fetch wrappers.
reset()
r = sh(f"patch -p1 < {OLD_CHECKS}/pass_alt_fetch_primitives.patch", check=False)
assert r.returncode == 0, r.stdout + r.stderr
patch_alt_fetch()
sh("git add -A")
sh(f"git diff inj > {OUT}/pass_alt_fetch_primitives_new.patch")
print("pass_alt_fetch_primitives_new.patch")

# blind: call the FetchState helper in the new modules.
reset()
r = sh(f"patch -p1 -l < {OLD_CHECKS}/blind.patch", check=False)
assert r.returncode == 0, r.stdout + r.stderr
patch_blind()
sh("git add -A")
sh(f"git diff inj > {OUT}/blind_new.patch")
print("blind_new.patch")

print("DONE")
