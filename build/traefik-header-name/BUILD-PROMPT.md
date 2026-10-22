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

Project root: `/home/mara/cwe-bench`. Task: `traefik-header-name`. Pattern: `B`. Track: `mined`.

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
- Advisory: GHSA-X677-9FXG-V5C5 / CVE-2026-54763 / GO-2026-6211 - traefik/traefik - header-name normalization mismatch leading to identity/authentication header spoofing (CWE-178/CWE-290/CWE-345). Whether a backend may trust an identity header (BasicAuth/DigestAuth headerField, ForwardAuth authResponseHeaders) that Traefik manages only in its dash/canonical form; at the pinned commit the auth middlewares delete only the canonical key
- Pinned (vulnerable) commit: 0056f09a0c4aff3cdd789bcad44a6dd196884180. Published fix: 108a5264473a2cbc8f12d6d691a3c6553cdf2c1b.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "19775",
 "advisory_ids": [
  "GHSA-X677-9FXG-V5C5",
  "CVE-2026-54763",
  "GO-2026-6211"
 ],
 "repo": "traefik/traefik",
 "pinned_commit": "unknown (parent of 108a5264473a2cbc8f12d6d691a3c6553cdf2c1b; parent_commit not given)",
 "fix_commits": [
  "108a5264473a2cbc8f12d6d691a3c6553cdf2c1b"
 ],
 "trust_decision": {
  "summary": "Whether a backend may trust an identity header (BasicAuth/DigestAuth headerField, ForwardAuth authResponseHeaders) that Traefik manages only in its dash/canonical form; at the pinned commit the auth middlewares delete only the canonical key, so a client-sent underscore variant (X_Auth_User) reaches backends that fold '_' to '-'. The published fix decides this at the entry point, via a new opt-in static option (default keep) that deletes or rejects every underscore header before routing.",
  "evidence": [
   "pkg/middlewares/auth/basic_auth.go:106-110",
   "pkg/middlewares/auth/digest_auth.go:100-104",
   "pkg/middlewares/auth/forward.go:197-216",
   "pkg/server/server_entrypoint_tcp.go:600-602",
   "fix.diff:371-380",
   "fix.diff:389-414"
  ]
 },
 "landing_point": {
  "where": "pkg/middlewares/auth/basic_auth.go:106-110",
  "why": "The summary names BasicAuth/DigestAuth/ForwardAuth headerField; this is where headerField is deleted with Header.Del (canonical key only) and re-set. The existing underscore-aware defence for X-Forwarded headers (pkg/middlewares/forwardedheaders/forwarded_header.go:52-65) also points a reader at per-middleware fixes."
 },
 "fix_sites": [
  {
   "where": "pkg/config/static/entrypoints.go:63-71",
   "entry_point": "static config / CLI flag --entrypoints.<name>.http.underscoreheadersstrategy (new HTTPConfig field, fix.diff:351)",
   "module_kind": "config schema (static configuration)"
  },
  {
   "where": "pkg/config/static/entrypoints.go:74-78",
   "entry_point": "static config defaults: HTTPConfig.SetDefaults sets keep (fix.diff:359)",
   "module_kind": "config defaults"
  },
  {
   "where": "fix.diff:320-328",
   "entry_point": "exported constants keep/delete/reject added to pkg/config/static/entrypoints.go",
   "module_kind": "config schema (static configuration)"
  },
  {
   "where": "pkg/server/server_entrypoint_tcp.go:602",
   "entry_point": "every HTTP request on an entry point (HTTP/1.1, h2c, HTTPS/HTTP2; HTTP/3 reuses the HTTPS handler at pkg/server/server_entrypoint_tcp_http3.go:54) via createHTTPServer handler chain (fix.diff:371-380)",
   "module_kind": "server handler-wrapper composition"
  },
  {
   "where": "pkg/server/server_entrypoint_tcp.go:699",
   "entry_point": "new removeHeadersWithUnderscores / rejectHeadersWithUnderscores wrappers inserted next to denyFragment (fix.diff:389-414)",
   "module_kind": "server request filter"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "pkg/server/server_entrypoint_tcp.go:600-602 (createHTTPServer handler chain, package pkg/server) plus pkg/config/static/entrypoints.go:63-78 \u2014 the published fix lives here, not in pkg/middlewares/auth where the report leads"
 },
 "O3_reason_to_dismiss": "Underscores are legal header-name characters and Traefik already Del()s the configured header; folding '_' into '-' is the backend's (CGI/WSGI/PHP) quirk, so a solver can argue the auth middlewares are correct and an entry-point-wide filter (or any change to default behaviour) is out of scope.",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Requests carrying legitimate underscore-named headers must still be forwarded unchanged by default (keep is the default and documented as preserving behaviour), and under delete the legitimate dash-form X-Auth-User must survive while only the underscore variant is dropped; an unconditional strip/reject breaks the keep default and the integration test expecting 409 under keep.",
  "where": "fix.diff:371-373, fix.diff:436-449, fix.diff:277-280, pkg/config/static/entrypoints.go:74-78"
 },
 "O6_input_shapes": [
  "fully underscored canonical-cased variant X_Auth_User alongside dash form (fix.diff:554-556)",
  "mixed underscore/dash variant X_Auth-User (fix.diff:559-561)",
  "non-canonical lower-case underscore variant x_auth_user (fix.diff:564-566)",
  "header named only '_' (fix.diff:569-571)",
  "multi-value dash header kept intact (fix.diff:549-551)",
  "strategy values: unset/empty, keep, delete, reject, invalid value -> startup error (fix.diff:371-380)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "pkg/config/static/entrypoints.go:63-78 (HTTPConfig schema + SetDefaults) feeding pkg/server/server_entrypoint_tcp.go:552 createHTTPServer",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "BasicAuth headerField: Header.Del removes only the canonical key, underscore variant of the identity header passes through under the default keep strategy",
   "where": "pkg/middlewares/auth/basic_auth.go:106-110",
   "reason_to_dismiss": "Operators are expected to enable underscoreHeadersStrategy on the entry point; middleware is 'not responsible' for backend name folding",
   "distance": "pkg/middlewares/auth vs fix in pkg/server",
   "present_in_latest": "yes",
   "latest_where": "latest/pkg/middlewares/auth/basic_auth.go:106-111"
  },
  {
   "route": "DigestAuth headerField: same canonical-only delete, underscore variant forwarded under default keep",
   "where": "pkg/middlewares/auth/digest_auth.go:100-104",
   "reason_to_dismiss": "Same as BasicAuth; covered only when the opt-in entry-point option is set",
   "distance": "same package as BasicAuth; fix in pkg/server",
   "present_in_latest": "yes",
   "latest_where": "latest/pkg/middlewares/auth/digest_auth.go:99-104"
  },
  {
   "route": "ForwardAuth authResponseHeaders list and authResponseHeadersRegex: deletes canonical names / regex-matched keys only; underscore variants of listed headers survive under default keep",
   "where": "pkg/middlewares/auth/forward.go:197-216",
   "reason_to_dismiss": "Regex users choose their own pattern; list entries are canonicalized by design; entry-point option is the documented mitigation",
   "distance": "pkg/middlewares/auth/forward.go; fix in pkg/server",
   "present_in_latest": "yes",
   "latest_where": "latest/pkg/middlewares/auth/forward.go:322-338"
  },
  {
   "route": "Headers middleware customRequestHeaders with empty value (delete a client header, e.g. an identity header) removes only the canonical form",
   "where": "pkg/middlewares/headers/header.go:129-130",
   "reason_to_dismiss": "Neighbouring feature not named in the advisory (only Basic/Digest/ForwardAuth are)",
   "distance": "pkg/middlewares/headers, different package from landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/pkg/middlewares/headers/header.go:129"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "pkg/middlewares/auth/forward.go:133-135",
   "sibling": "authRequestHeaders copy to the auth server matching canonical names only, letting an underscore variant reach the auth service",
   "why_realistic": "writeHeader/oldWriteHeader filter by canonical name, same idiom as authResponseHeaders"
  },
  {
   "where": "pkg/middlewares/passtlsclientcert/pass_tls_client_cert.go:153",
   "sibling": "PassTLSClientCert sets X-Forwarded-Tls-Client-Cert with Header.Set; a version that deletes only the canonical form before setting would leave X_Forwarded_Tls_Client_Cert",
   "why_realistic": "underscore stripping for this header lives in a different package (forwardedheaders XHeadersSet, pkg/middlewares/forwardedheaders/forwarded_header.go:34-46) and only runs for untrusted IPs"
  }
 ],
 "O9_family": "header-name normalization mismatch leading to identity/authentication header spoofing (CWE-178/CWE-290/CWE-345)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.25 (go.mod:3, module github.com/traefik/traefik/v2)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "pkg/server/server_entrypoint_tcp_test.go (unit, runs createHTTPServer/NewTCPEntryPoint in-process); pkg/middlewares/auth/*_test.go; integration/simple_test.go (needs built traefik binary, local only)"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "pkg/config/static/entrypoints.go, pkg/server/server_entrypoint_tcp.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "In basic_auth/digest_auth only, also delete the underscore spelling of headerField (exact X_Auth_User), missing mixed/lower-case variants and the ForwardAuth list/regex routes."
 },
 "out_of_scope_notes": [
  "removeHeadersWithUnderscores comment says 'header and trailer' (fix.diff:389, 402) but only req.Header is iterated; request trailers not examined.",
  "Latest tree also has an AliasHeadersStrategy option (latest/pkg/server/server_entrypoint_tcp.go:239-246), a later related change not screened."
 ],
 "unverified": [
  "Biggest concern (not an O12 enum): the published fix is a new opt-in static option with default 'keep', so default behaviour is unchanged; hidden tests derived from it require the solver to invent the exact option name/values, unless the report specifies that API. A fair task would likely need per-middleware tests instead, diverging from the published fix.",
  "repo_mb not measured (no shell); traefik with webui is likely tens to low hundreds of MB.",
  "O1 counts the three middleware routes named in the advisory (BasicAuth, DigestAuth, ForwardAuth); the fix itself is a single entry-point filter.",
  "Whether Go's net/http server preserves the non-canonical key x_auth_user verbatim in req.Header was not run-checked; the fix tests imply it does (fix.diff:525).",
  "pinned commit hash not provided in inputs.",
  "O11 estimate assumes per-middleware remediation plus an entry-point option; the published-only fix is ~20 minutes."
 ]
}
  ```
- Published fix sites:   - pkg/config/static/entrypoints.go:63-71 — entry point: static config / CLI flag --entrypoints.<name>.http.underscoreheadersstrategy (new HTTPConfig field, fix.diff:351) [config schema (static configuration)]
  - pkg/config/static/entrypoints.go:74-78 — entry point: static config defaults: HTTPConfig.SetDefaults sets keep (fix.diff:359) [config defaults]
  - fix.diff:320-328 — entry point: exported constants keep/delete/reject added to pkg/config/static/entrypoints.go [config schema (static configuration)]
  - pkg/server/server_entrypoint_tcp.go:602 — entry point: every HTTP request on an entry point (HTTP/1.1, h2c, HTTPS/HTTP2; HTTP/3 reuses the HTTPS handler at pkg/server/server_entrypoint_tcp_http3.go:54) via createHTTPServer handler chain (fix.diff:371-380) [server handler-wrapper composition]
  - pkg/server/server_entrypoint_tcp.go:699 — entry point: new removeHeadersWithUnderscores / rejectHeadersWithUnderscores wrappers inserted next to denyFragment (fix.diff:389-414) [server request filter]
- Uncovered routes to confirm (pattern B):   - pkg/middlewares/auth/basic_auth.go:106-110 — BasicAuth headerField: Header.Del removes only the canonical key, underscore variant of the identity header passes through under the default keep strategy (reason to dismiss: Operators are expected to enable underscoreHeadersStrategy on the entry point; middleware is 'not responsible' for backend name folding; still in latest: yes)
  - pkg/middlewares/auth/digest_auth.go:100-104 — DigestAuth headerField: same canonical-only delete, underscore variant forwarded under default keep (reason to dismiss: Same as BasicAuth; covered only when the opt-in entry-point option is set; still in latest: yes)
  - pkg/middlewares/auth/forward.go:197-216 — ForwardAuth authResponseHeaders list and authResponseHeadersRegex: deletes canonical names / regex-matched keys only; underscore variants of listed headers survive under default keep (reason to dismiss: Regex users choose their own pattern; list entries are canonicalized by design; entry-point option is the documented mitigation; still in latest: yes)
  - pkg/middlewares/headers/header.go:129-130 — Headers middleware customRequestHeaders with empty value (delete a client header, e.g. an identity header) removes only the canonical form (reason to dismiss: Neighbouring feature not named in the advisory (only Basic/Digest/ForwardAuth are); still in latest: yes)
- Design plan from the lead: MAIN LEVER: the published fix must be reproduced in full. The hidden tests require closing EVERY published fix site through its real entry point, including the site that looks out of scope (wrapper_or_composition at pkg/server/server_entrypoint_tcp.go:600-602 (createHTTPServer handler chain, pac; a solver may dismiss it because: Underscores are legal header-name characters and Traefik already Del()s the configured header; folding '_' into '-' is the backend's (CGI/WSGI/PHP) quirk, so a solver can argue the auth middlewares ar). The tempting wrong fix that must FAIL: In basic_auth/digest_auth only, also delete the underscore spelling of headerField (exact X_Auth_User), missing mixed/lower-case variants and the ForwardAuth list/regex routes..

INPUT-SHAPE / ROUTE VARIANTS (one security test each, driven through the real entry point, failing on the pinned code and passing on a correct fix): fully underscored canonical-cased variant X_Auth_User alongside dash form (fix.diff:554-556); mixed underscore/dash variant X_Auth-User (fix.diff:559-561); non-canonical lower-case underscore variant x_auth_user (fix.diff:564-566); header named only '_' (fix.diff:569-571); multi-value dash header kept intact (fix.diff:549-551); strategy values: unset/empty, keep, delete, reject, invalid value -> startup error (fix.diff:371-380).

PRODUCER OFF THE CHECK'S PATH: the state is produced by a config_loader at pkg/config/static/entrypoints.go:63-78 (HTTPConfig schema + SetDefaults) feeding that the check does not call; a fix only at the check misses it.

PATTERN B UNCOVERED ROUTES - confirm each with a behavioural test on the pinned copy before relying on it, then add one row per route to build/audit/uncovered-routes.tsv: pkg/middlewares/auth/basic_auth.go:106-110 (dismiss: Operators are expected to enable underscoreHeadersStrategy on the entry point; m; latest=yes); pkg/middlewares/auth/digest_auth.go:100-104 (dismiss: Same as BasicAuth; covered only when the opt-in entry-point option is set; latest=yes); pkg/middlewares/auth/forward.go:197-216 (dismiss: Regex users choose their own pattern; list entries are canonicalized by design; ; latest=yes); pkg/middlewares/headers/header.go:129-130 (dismiss: Neighbouring feature not named in the advisory (only Basic/Digest/ForwardAuth ar; latest=yes). These are unmodified upstream code the published fix did not touch; the task's reference fix closes them too.

COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): Requests carrying legitimate underscore-named headers must still be forwarded unchanged by default (keep is the default and documented as preserving behaviour), and under delete the legitimate dash-form X-Auth-User must  (near fix.diff:371-373, fix.diff:436-449, fix.diff:277-280, pkg/co).

Aim for at least two levers with DIFFERENT reasons to dismiss. instruction.md stays at product level: state the system, one observed impact with one user-level trigger, and the security property as invariants worded to cover every tested route and shape; keep legitimate use working; never name files/functions/fields/CVEs (put every such identifier in manifest.leak_terms).
- Host notes: Language: Go. Offline after build (no external services). Security logic is testable without a live server/cluster - call the validation/transform functions directly with crafted inputs. The project's own tests for the area must pass at the pinned commit. Confirm each pattern-B route with a test on the pinned copy; most are fixed in current upstream. Pin at the given vulnerable commit; keep any unrelated earlier fixes present.

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

## Environment (`tasks/traefik-header-name/environment/Dockerfile`)
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

## Report to the solver (`tasks/traefik-header-name/instruction.md`)
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

## Tests (`tasks/traefik-header-name/tests/`)
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
- **Wrong-fix patches** go in `build/traefik-header-name/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/traefik-header-name/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/traefik-header-name/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/traefik-header-name/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py traefik-header-name --only static
python3 -I builder/gate.py traefik-header-name --only nop
python3 -I builder/gate.py traefik-header-name --only oracle
python3 -I builder/gate.py traefik-header-name --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/traefik-header-name/`;
  - edit only `tasks/traefik-header-name/`, `build/traefik-header-name/` and, for pattern B, the register;
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
