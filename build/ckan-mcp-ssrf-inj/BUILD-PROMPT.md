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

Project root: `/home/mara/cwe-bench`. Task: `ckan-mcp-ssrf-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-798P-78G2-V556 / CVE-2026-61612 - ondata/ckan-mcp-server - SSRF (CWE-918): hostname-string check vs resolved IP / redirect target. Whether a caller-supplied server_url / SPARQL endpoint URL may be fetched is decided only by a string check on the hostname in validateServerUrl (src/
- Pinned (vulnerable) commit: 129ba172ec15429347ea1faf5c919af730720370. Published fix: bb7439b553b9f965adc3d43bcd415c42eebe2f40.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "9429",
 "advisory_ids": [
  "GHSA-798P-78G2-V556",
  "CVE-2026-61612"
 ],
 "repo": "ondata/ckan-mcp-server",
 "pinned_commit": "parent of bb7439b553b9f965adc3d43bcd415c42eebe2f40 (parent_commit not given; tree at /home/mara/screen5/hosts/9429/repo, version 0.4.107)",
 "fix_commits": [
  "bb7439b553b9f965adc3d43bcd415c42eebe2f40"
 ],
 "trust_decision": {
  "summary": "Whether a caller-supplied server_url / SPARQL endpoint URL may be fetched is decided only by a string check on the hostname in validateServerUrl (src/utils/http.ts), called from makeCkanRequest and querySparqlEndpoint; the resolved IP the socket connects to is never checked.",
  "evidence": [
   "src/utils/http.ts:245-308",
   "src/utils/http.ts:340",
   "src/tools/sparql.ts:48"
  ]
 },
 "landing_point": {
  "where": "src/utils/http.ts:245",
  "why": "The summary says 'incomplete fix of CVE-2026-53509' / 'DNS-name to internal IP'; validateServerUrl is the named SSRF guard and the obvious place to add resolution."
 },
 "fix_sites": [
  {
   "where": "src/utils/http.ts:268-300",
   "entry_point": "every CKAN MCP tool/resource taking server_url (e.g. package_search) via makeCkanRequest; sparql_query",
   "module_kind": "shared guard (literal-IP check refactored into isBlockedIp, fix.diff:112-139, fix.diff:170-192)"
  },
  {
   "where": "src/utils/http.ts:387",
   "entry_point": "all makeCkanRequest-based MCP tools and resources (Node runtime)",
   "module_kind": "HTTP client wrapper: SSRF-safe DNS lookup agent + maxRedirects (fix.diff:242-296, fix.diff:341-349)"
  },
  {
   "where": "src/tools/sparql.ts:48-52",
   "entry_point": "MCP tool sparql_query (endpoint_url)",
   "module_kind": "second implementation: separate fetch-based client, pre-resolution check (fix.diff:75-76, fix.diff:312-332)"
  },
  {
   "where": "src/transport/http.ts:9",
   "entry_point": "HTTP transport startup (POST /mcp server)",
   "module_kind": "transport/config gate: refuse to start without CKAN_ALLOWED_DOMAINS (fix.diff:91-93, fix.diff:205-224)"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/tools/sparql.ts:47-92 (fetch-based client with its own request code, separate from makeCkanRequest in src/utils/http.ts:330)"
 },
 "O3_reason_to_dismiss": "sparql_query is HTTPS-only and a non-CKAN neighbouring feature, and the Workers fetch path runs in the Cloudflare sandbox that 'already blocks internal addresses' (fix.diff:13), so a solver can argue both are outside the CKAN/Node path the report describes.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Public hostnames (dati.gov.it etc.) and portals remapped by getPortalApiUrlForHostname must keep working; DNS failures must not be turned into a blanket block, Workers runtime has no node:dns, and IPv6/public IPs like 172.15.x / 100.63.x must stay allowed (fix.diff:428-431).",
  "where": "src/utils/http.ts:342-351"
 },
 "O6_input_shapes": [
  "IPv4 literal",
  "bracketed IPv6 literal",
  "hostname resolving to private IPv4 (single A record)",
  "hostname with multiple records where any is internal (fix.diff:464-469)",
  "IPv4-mapped IPv6 resolved address",
  "lookup called with options.all vs single-address callback (fix.diff:264-268)",
  "lookup called with callback as second arg (fix.diff:244-247)",
  "redirect hops on axios path via pinned lookup (only for hostname targets)"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "src/utils/http.ts:387 (axios.get resolves the name and connects; the check at src/utils/http.ts:245 never calls the resolver)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "sparql_query fetch follows redirects (default) to any host; fix only pre-checks the first hostname",
   "where": "src/tools/sparql.ts:70-90",
   "reason_to_dismiss": "Endpoint is HTTPS-only and a pre-resolution check was added, so it looks done",
   "distance": "other file (src/tools) from landing point (src/utils/http.ts)",
   "present_in_latest": "no",
   "latest_where": "latest/src/tools/sparql.ts:73"
  },
  {
   "route": "non-Node (Workers) fetch branch of makeCkanRequest gets no resolution/redirect check",
   "where": "src/utils/http.ts:408-435",
   "reason_to_dismiss": "Cloudflare sandbox is said to block internal egress (fix.diff:13)",
   "distance": "same file, other branch",
   "present_in_latest": "no",
   "latest_where": "latest/src/utils/http.ts:841-842"
  },
  {
   "route": "axios redirect to an IP-literal target skips the custom lookup, so redirect-to-127.0.0.1 is not checked after the published fix",
   "where": "src/utils/http.ts:387-402",
   "reason_to_dismiss": "The pinned lookup agent appears to cover all connections, including redirects (fix.diff:12 claims redirect-to-internal is closed)",
   "distance": "same file",
   "present_in_latest": "no",
   "latest_where": "latest/src/utils/http.ts:795-799"
  },
  {
   "route": "sparql pre-resolution then fetch re-resolves (rebinding window) and the check fails open on any DNS error",
   "where": "src/tools/sparql.ts:48-76",
   "reason_to_dismiss": "fetch cannot take a lookup agent; fail-open is documented as intended for Workers (fix.diff:321-322)",
   "distance": "other file",
   "present_in_latest": "unknown",
   "latest_where": "latest/src/utils/http.ts:591"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/tools/quality.ts:425-438",
   "sibling": "MQA lookup building its URL from a per-portal configurable base instead of the constant MQA_API_BASE",
   "why_realistic": "Portal config already carries per-portal endpoints (src/utils/portal-config.ts:88-94); latest moved this fetch onto safeFetch (latest/src/tools/quality.ts:570), suggesting it became a reachable route."
  },
  {
   "where": "src/utils/portal-config.ts:73-80",
   "sibling": "resolvedServerUrl from api_url_aliases / user-supplied portal overrides fetched without re-validation",
   "why_realistic": "makeCkanRequest validates serverUrl but requests resolvedServerUrl (src/utils/http.ts:340-356); a maintainer adding user-configurable portals would plausibly skip the re-check."
  }
 ],
 "O9_family": "SSRF (CWE-918): hostname-string check vs resolved IP / redirect target",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (ESM, Node >=18)",
  "toolchain": "npm, esbuild, vitest (package.json:12-22)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/unit/http.test.ts (validateServerUrl, makeCkanRequest with mocked axios) and tests/integration/sparql.test.ts (fetch stubbed); DNS injectable via test seams in the fix"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/utils/http.ts, src/tools/sparql.ts, src/transport/http.ts (plus version bumps in src/server.ts, src/worker.ts)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a dns.lookup + isBlockedIp check inside validateServerUrl / makeCkanRequest only, leaving sparql_query, redirects and the fetch branch unchecked (and TOCTOU-prone)."
 },
 "out_of_scope_notes": [
  "transport/http.ts serves POST /mcp with no authentication (src/transport/http.ts:13-27); the fix adds only an allowlist gate, not auth.",
  "isBlockedIp misses some special ranges (e.g. 198.18.0.0/15, 224.0.0.0/4, IPv6 ::ffff hex forms in other notations); not pursued."
 ],
 "unverified": [
  "pinned_commit SHA not provided; assumed the given tree is the fix's parent (package.json:3 shows 0.4.107, matching fix.diff:28).",
  "repo size in MB not measured; codebase is small (~38 .ts files under src/), tiny_repo flag may hold but was not verified.",
  "O8 routes were inferred from later upstream changes (latest/src/utils/http.ts:666-707, 795-799) and sibling-advisory count; their advisory IDs were not checked.",
  "Whether Node's http Agent lookup is skipped for IP-literal redirect targets is taken from the latest code comment (latest/src/utils/http.ts:795), not verified against Node source.",
  "O13 recall risk estimated; write-up coverage not checked (no network)."
 ]
}
  ```
- Published fix sites:   - src/utils/http.ts:268-300 — entry point: every CKAN MCP tool/resource taking server_url (e.g. package_search) via makeCkanRequest; sparql_query [shared guard (literal-IP check refactored into isBlockedIp, fix.diff:112-139, fix.diff:170-192)]
  - src/utils/http.ts:387 — entry point: all makeCkanRequest-based MCP tools and resources (Node runtime) [HTTP client wrapper: SSRF-safe DNS lookup agent + maxRedirects (fix.diff:242-296, fix.diff:341-349)]
  - src/tools/sparql.ts:48-52 — entry point: MCP tool sparql_query (endpoint_url) [second implementation: separate fetch-based client, pre-resolution check (fix.diff:75-76, fix.diff:312-332)]
  - src/transport/http.ts:9 — entry point: HTTP transport startup (POST /mcp server) [transport/config gate: refuse to start without CKAN_ALLOWED_DOMAINS (fix.diff:91-93, fix.diff:205-224)]
- Uncovered routes to confirm (pattern B):   - src/tools/sparql.ts:70-90 — sparql_query fetch follows redirects (default) to any host; fix only pre-checks the first hostname (reason to dismiss: Endpoint is HTTPS-only and a pre-resolution check was added, so it looks done; still in latest: no)
  - src/utils/http.ts:408-435 — non-Node (Workers) fetch branch of makeCkanRequest gets no resolution/redirect check (reason to dismiss: Cloudflare sandbox is said to block internal egress (fix.diff:13); still in latest: no)
  - src/utils/http.ts:387-402 — axios redirect to an IP-literal target skips the custom lookup, so redirect-to-127.0.0.1 is not checked after the published fix (reason to dismiss: The pinned lookup agent appears to cover all connections, including redirects (fix.diff:12 claims redirect-to-internal is closed); still in latest: no)
  - src/tools/sparql.ts:48-76 — sparql pre-resolution then fetch re-resolves (rebinding window) and the check fails open on any DNS error (reason to dismiss: fetch cannot take a lookup agent; fail-open is documented as intended for Workers (fix.diff:321-322); still in latest: unknown)
- Design plan from the lead: TRACK = INJECTED (breaker recipe; mined tasks were all solved, injected-sibling tasks at a recurring check broke both models).

RECURRING CHECK / PROTECTED SINK: Whether a caller-supplied server_url / SPARQL endpoint URL may be fetched is decided only by a string check on the hostname in validateServerUrl (src/utils/http.ts), called from makeCkanRequest and querySparqlEndpoint; the resolved IP the socket connects to is

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: src/tools/sparql.ts:70-90 (sparql_query fetch follows redirects (default) to any h; skip: Endpoint is HTTPS-only and a pre-resolution c); src/utils/http.ts:408-435 (non-Node (Workers) fetch branch of makeCkanRequest gets; skip: Cloudflare sandbox is said to block internal ); src/utils/http.ts:387-402 (axios redirect to an IP-literal target skips the custom; skip: The pinned lookup agent appears to cover all ); src/tools/sparql.ts:48-76 (sparql pre-resolution then fetch re-resolves (rebinding; skip: fetch cannot take a lookup agent; fail-open i).
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): src/tools/quality.ts:425-438 -> MQA lookup building its URL from a per-portal configurable base instea (realistic: Portal config already carries per-portal endpoints (src/util); src/utils/portal-config.ts:73-80 -> resolvedServerUrl from api_url_aliases / user-supplied portal override (realistic: makeCkanRequest validates serverUrl but requests resolvedSer). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Public hostnames (dati.gov.it etc.) and portals remapped by getPortalApiUrlForHostname must keep working; DNS failures must not be turned into a blanket block, Workers runtime has no node:dns, and IPv (near src/utils/http.ts:342-351); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: TypeScript (ESM, Node >=18). Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (2 entry points). Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes. If the repo is a large monorepo, scope the build/tests to the affected package only.

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

## Environment (`tasks/ckan-mcp-ssrf-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/ckan-mcp-ssrf-inj/instruction.md`)
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

## Tests (`tasks/ckan-mcp-ssrf-inj/tests/`)
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
- **Wrong-fix patches** go in `build/ckan-mcp-ssrf-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/ckan-mcp-ssrf-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/ckan-mcp-ssrf-inj/manifest.json`:**
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

**Also in `build/ckan-mcp-ssrf-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py ckan-mcp-ssrf-inj --only static
python3 -I builder/gate.py ckan-mcp-ssrf-inj --only nop
python3 -I builder/gate.py ckan-mcp-ssrf-inj --only oracle
python3 -I builder/gate.py ckan-mcp-ssrf-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/ckan-mcp-ssrf-inj/`;
  - edit only `tasks/ckan-mcp-ssrf-inj/`, `build/ckan-mcp-ssrf-inj/` and, for pattern B, the register;
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
