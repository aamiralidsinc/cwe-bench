# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `nginxui-origin-inj`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: GHSA-9H23-53F4-Q947 / CVE-2026-107804 - 0xjacky/nginx-ui - CWE-346 origin validation: client-IP trust / forwarded-header trust boundary (IP allowlist bypass, shared login lockout). Which peer may supply the client IP (X-Forwarded-For/X-Real-IP) is decided once, engine-wide, by gin SetTrustedProxies in InitRouter; at the pinned co
- Pinned (vulnerable) commit: ece8c62c512378eb8360bf8d6d31bec7468f15bb. Published fix: e30e331303fc21cf077a2bea724bd79e66892eaf.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "16906",
 "advisory_ids": [
  "GHSA-9H23-53F4-Q947",
  "CVE-2026-107804"
 ],
 "repo": "0xjacky/nginx-ui",
 "pinned_commit": "parent of e30e331303fc21cf077a2bea724bd79e66892eaf (parent_commit null in candidate)",
 "fix_commits": [
  "e30e331303fc21cf077a2bea724bd79e66892eaf"
 ],
 "trust_decision": {
  "summary": "Which peer may supply the client IP (X-Forwarded-For/X-Real-IP) is decided once, engine-wide, by gin SetTrustedProxies in InitRouter; at the pinned commit nothing is trusted, so behind the bundled Docker nginx every request has ClientIP 127.0.0.1, which the IP allowlist exempts and the login ban keys on as one shared bucket.",
  "evidence": [
   "router/routers.go:47",
   "internal/middleware/ip_whitelist.go:13-14",
   "api/user/auth.go:51-56",
   "api/user/auth.go:74",
   "resources/docker/nginx-ui.conf:28-29",
   "resources/docker/nginx-ui.conf:35",
   "Dockerfile:10"
  ]
 },
 "landing_point": {
  "where": "internal/middleware/ip_whitelist.go:14",
  "why": "The summary names IP allowlists and the loopback exemption is visible here; the lockout half leads to api/user/auth.go:51. The real cause is the engine trusted-proxy setting in another package (router/routers.go:47)."
 },
 "fix_sites": [
  {
   "where": "router/routers.go:47",
   "entry_point": "every HTTP route on the cosy/gin engine (engine-level SetTrustedProxies; fix.diff:1824-1827)",
   "module_kind": "router/engine bootstrap (defaults)"
  },
  {
   "where": "fix.diff:1663-1682",
   "entry_point": "same engine-wide; new router/client_ip.go picks trusted proxies by topology via helper.ShouldManageBundledNginx (internal/helper/docker.go:21-24)",
   "module_kind": "router/topology default (new file)"
  },
  {
   "where": "settings/auth.go:3-7",
   "entry_point": "app.ini [auth] / env NGINX_UI_AUTH_TRUSTED_PROXIES; POST /api/settings binding (fix.diff:1839 adds TrustedProxies with ip|cidr|redacted, protected)",
   "module_kind": "settings schema / config loader"
  },
  {
   "where": "internal/middleware/ip_whitelist.go:14",
   "entry_point": "/api/* group (router/routers.go:64), /mcp and /mcp_message (mcp/router.go:39, mcp/router.go:43), embedded static (router/routers_embed.go:16); fix drops the empty-ClientIP fail-open (fix.diff:1409-1410)",
   "module_kind": "HTTP middleware"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "router/routers.go:47 (engine default SetTrustedProxies(nil); the fix replaces it with a topology-aware default merged with the configured TrustedProxies, fix.diff:1663-1682)"
 },
 "O3_reason_to_dismiss": "The router bootstrap looks like generic framework setup, and `SetTrustedProxies(nil)` reads as already hardened. A solver could argue the bug is the loopback exemption in the middleware and leave the proxy topology alone.",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Direct loopback clients must still pass the allowlist. X-Forwarded-For/X-Real-IP from untrusted peers must still be ignored. Deployments without the bundled nginx (NGINX_UI_DISABLE_BUNDLED_NGINX, non-Docker) must not start trusting loopback. Trusting all proxies, or removing the loopback exemption, breaks one of these.",
  "where": "internal/middleware/ip_whitelist.go:14; internal/helper/docker.go:21-24; router/routers.go:47"
 },
 "O6_input_shapes": [
  "single X-Forwarded-For value via the bundled loopback proxy",
  "X-Real-IP only",
  "IPv6 loopback peer ::1 with an IPv6 forwarded client",
  "multi-hop X-Forwarded-For chain, stopping at the first untrusted hop",
  "spoofed X-Forwarded-For from an untrusted direct peer",
  "invalid/unparseable RemoteAddr giving an empty ClientIP (now fails closed)",
  "TrustedProxies entries as IP or CIDR, plus the redacted placeholder on settings save"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "settings/auth.go:3-12 (AuthSettings, loaded from app.ini/env; the fix adds TrustedProxies) consumed once at router/routers.go:47 at startup",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "internal/middleware/middleware.go:182",
   "sibling": "The node-auth failure log could read X-Real-IP / X-Forwarded-For directly instead of ClientIP().",
   "why_realistic": "Diagnostic logging that wants the 'real' client behind a proxy often reads the header directly, bypassing the engine trust list."
  },
  {
   "where": "api/user/passkey.go:239-241",
   "sibling": "Passkey login ban-clear (or an OTP/2FA attempt limiter) keyed on c.Request.RemoteAddr or a raw header.",
   "why_realistic": "A second auth entry point written separately from Login could pick a different client-IP source; it would still be shared 127.0.0.1 behind the bundled proxy."
  },
  {
   "where": "mcp/router.go:39",
   "sibling": "The MCP route could use its own allowlist helper that trusts X-Forwarded-For from any peer.",
   "why_realistic": "MCP is registered on the engine outside the /api group with its own middleware chain, so a separate implementation there is plausible."
  }
 ],
 "O9_family": "CWE-346 origin validation: client-IP trust / forwarded-header trust boundary (IP allowlist bypass, shared login lockout)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (backend); TypeScript/Vue (frontend, unrelated to the security change)",
  "toolchain": "go 1.27.1 (go.mod:3), gin v1.12.0 (go.mod:30), uozi-tech/cosy v1.34.1 (go.mod:61); sqlite via gorm for tests",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Go tests for this area: internal/middleware/*_test.go (e.g. internal/middleware/middleware_test.go:109 sets RemoteAddr), api/user security tests, settings/restore and settings tests. Tests added by the fix: internal/middleware/ip_whitelist_test.go, router/client_ip_test.go, internal/user/login_ban_test.go. Hidden tests can drive gin.New()+configureTrustedProxies or InitRouter with httptest offline."
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "injection_only",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "router/routers.go, router/client_ip.go (new), settings/auth.go, internal/middleware/ip_whitelist.go",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Remove the 127.0.0.1/::1 exemption in IPWhiteList, or drop SetTrustedProxies(nil) so gin trusts every proxy, which makes X-Forwarded-For spoofable from any peer."
 },
 "out_of_scope_notes": [
  "The fix commit is a release bundle: most of the diff is unrelated frontend work (session expiry, error normalization, nginx performance) and docs; c_same_check_name 'expireSession' is frontend noise, not part of this protection.",
  "The IP allowlist matches exact strings only (lo.Contains at internal/middleware/ip_whitelist.go:19); no CIDR support, and IPv4-mapped IPv6 forms are not normalized.",
  "Cluster Proxy middleware forwards requests to remote nodes, which see the controller's IP, not the browser's; a separate trust topology."
 ],
 "unverified": [
  "repo_mb: repository size not measured (no shell use); tiny_repo/giant_repo not assessed but the tree looks large (Go backend + Vue app + docs).",
  "pinned_commit SHA is not given in the inputs (parent_commit null); recorded as the parent of the fix commit.",
  "Did not confirm whether cosy registers any other gin engine or listener in production outside router/routers.go:41; grep found only cosy.GetEngine there.",
  "recall_risk 'low' rests on the publish date (2026-10-09) only; external write-ups were not checked (no network).",
  "O8 is empty because every client-IP consumer (internal/middleware/ip_whitelist.go:13, api/user/auth.go:51, api/user/passkey.go:100, api/user/passkey.go:239, internal/middleware/middleware.go:182) uses c.ClientIP() on the single engine, so the engine-level fix covers them all; no raw header reads were found in Go sources."
 ]
}
  ```
- Published fix sites:   - router/routers.go:47 — entry point: every HTTP route on the cosy/gin engine (engine-level SetTrustedProxies; fix.diff:1824-1827) [router/engine bootstrap (defaults)]
  - fix.diff:1663-1682 — entry point: same engine-wide; new router/client_ip.go picks trusted proxies by topology via helper.ShouldManageBundledNginx (internal/helper/docker.go:21-24) [router/topology default (new file)]
  - settings/auth.go:3-7 — entry point: app.ini [auth] / env NGINX_UI_AUTH_TRUSTED_PROXIES; POST /api/settings binding (fix.diff:1839 adds TrustedProxies with ip|cidr|redacted, protected) [settings schema / config loader]
  - internal/middleware/ip_whitelist.go:14 — entry point: /api/* group (router/routers.go:64), /mcp and /mcp_message (mcp/router.go:39, mcp/router.go:43), embedded static (router/routers_embed.go:16); fix drops the empty-ClientIP fail-open (fix.diff:1409-1410) [HTTP middleware]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: TRACK = INJECTED (breaker recipe; mined tasks were all solved, injected-sibling tasks at a recurring check broke both models).

RECURRING CHECK / PROTECTED SINK: Which peer may supply the client IP (X-Forwarded-For/X-Real-IP) is decided once, engine-wide, by gin SetTrustedProxies in InitRouter; at the pinned commit nothing is trusted, so behind the bundled Docker nginx every request has ClientIP 127.0.0.1, which the IP

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: none noted.
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): internal/middleware/middleware.go:182 -> The node-auth failure log could read X-Real-IP / X-Forwarded-For direc (realistic: Diagnostic logging that wants the 'real' client behind a pro); api/user/passkey.go:239-241 -> Passkey login ban-clear (or an OTP/2FA attempt limiter) keyed on c.Req (realistic: A second auth entry point written separately from Login coul); mcp/router.go:39 -> The MCP route could use its own allowlist helper that trusts X-Forward (realistic: MCP is registered on the engine outside the /api group with ). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Direct loopback clients must still pass the allowlist. X-Forwarded-For/X-Real-IP from untrusted peers must still be ignored. Deployments without the bundled nginx (NGINX_UI_DISABLE_BUNDLED_NGINX, non- (near internal/middleware/ip_whitelist.go:14; internal/h); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Go (backend); TypeScript/Vue (frontend, unrelated to the security change). Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (5 entry points). Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes. If the repo is a large monorepo, scope the build/tests to the affected package only.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/nginxui-origin-inj/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/nginxui-origin-inj/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/nginxui-origin-inj/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/nginxui-origin-inj/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/nginxui-origin-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/nginxui-origin-inj/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/nginxui-origin-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py nginxui-origin-inj --only static
python3 -I builder/gate.py nginxui-origin-inj --only nop
python3 -I builder/gate.py nginxui-origin-inj --only oracle
python3 -I builder/gate.py nginxui-origin-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/nginxui-origin-inj/`;
  - edit only `tasks/nginxui-origin-inj/`, `build/nginxui-origin-inj/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
