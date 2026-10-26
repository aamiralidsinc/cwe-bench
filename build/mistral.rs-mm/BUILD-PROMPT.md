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

Project root: `/home/mara/cwe-bench`. Task: `mistral.rs-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-WFGQ-W7CQ-QJ7J"]; ericlbuehler/mistral.rs; SSRF plus arbitrary local file read through an untrusted media source URL or path (CWE-918, CWE-73)
- Pinned (vulnerable) commit: unknown (parent of 74793379649febc758b6a0d4b71aa6aeabc80f9c; parent_commit not given). Published fix: 74793379649febc758b6a0d4b71aa6aeabc80f9c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "21576",
 "advisory_ids": [
  "GHSA-WFGQ-W7CQ-QJ7J"
 ],
 "repo": "ericlbuehler/mistral.rs",
 "pinned_commit": "unknown (parent of 74793379649febc758b6a0d4b71aa6aeabc80f9c; parent_commit not given)",
 "fix_commits": [
  "74793379649febc758b6a0d4b71aa6aeabc80f9c"
 ],
 "trust_decision": {
  "summary": "Whether a media source string from an HTTP request body (image/audio/video url, input_file file_url) may name a server-local file or a private/internal network host. At the pinned commit this is decided nowhere for media (the shared loaders accept bare paths, file:// and any http host); input_file file_url has only a literal-host check, applied before redirects and DNS resolution.",
  "evidence": [
   "mistralrs-server-core/src/util.rs:45-87",
   "mistralrs-server-core/src/util.rs:91-131",
   "mistralrs-server-core/src/video.rs:51-84",
   "mistralrs-server-core/src/chat_completion.rs:927-953",
   "mistralrs-server-core/src/input_files.rs:94-164"
  ]
 },
 "landing_point": {
  "where": "mistralrs-server-core/src/util.rs:45",
  "why": "The summary names the media loader and image_url. parse_image_url is the function that accepts bare paths, file:// URLs (util.rs:48,65-75) and does an unrestricted reqwest::get (util.rs:61)."
 },
 "fix_sites": [
  {
   "where": "mistralrs-server-core/src/chat_completion.rs:931",
   "entry_point": "POST /v1/chat/completions, /v1/responses, /v1/messages, /v1/messages/count_tokens, MCP chat tool (all via chat_completion::parse_request)",
   "module_kind": "HTTP request parser (call site switched to the server-policy loader for images)"
  },
  {
   "where": "mistralrs-server-core/src/chat_completion.rs:940",
   "entry_point": "same parse_request routes, audio_url parts",
   "module_kind": "HTTP request parser (audio call site)"
  },
  {
   "where": "mistralrs-server-core/src/chat_completion.rs:949",
   "entry_point": "same parse_request routes, video_url parts",
   "module_kind": "HTTP request parser (video call site)"
  },
  {
   "where": "mistralrs-server-core/src/util.rs:45",
   "entry_point": "public API mistralrs_server_core::util::parse_image_url (also CLI interactive mode, mistralrs-cli/src/commands/run/interactive.rs:329)",
   "module_kind": "shared media loader / lower-level public API (kept Local policy, server variant added)"
  },
  {
   "where": "mistralrs-server-core/src/util.rs:91",
   "entry_point": "public API util::parse_audio_url (CLI interactive.rs:345)",
   "module_kind": "shared media loader, audio variant"
  },
  {
   "where": "mistralrs-server-core/src/video.rs:51",
   "entry_point": "public API video::parse_video_url (CLI interactive.rs:361)",
   "module_kind": "separate video module loader (second copy of the same loading logic)"
  },
  {
   "where": "mistralrs-server-core/src/input_files.rs:94",
   "entry_point": "POST /v1/responses input_file.file_url (chat completions rejects file_url, chat_completion.rs:785-791) via resolve_input_file, chat_completion.rs:837",
   "module_kind": "neighbouring feature (input file attachment) with its own pre-existing literal-host guard"
  },
  {
   "where": "mistralrs-server-core/src/input_files.rs:74",
   "entry_point": "input_file.file_data on the same routes",
   "module_kind": "size limit on decode (resource limit, not the trust decision)"
  },
  {
   "where": "fix.diff:272-618",
   "entry_point": "new crate-private module media_source.rs (policy enum, DNS-resolve-then-pin, manual redirect re-validation, is_global_ip)",
   "module_kind": "new shared guard module"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "mistralrs-server-core/src/input_files.rs:94-164 (fetch_file_url + reject_private_host at input_files.rs:132-164: a separate fetcher with a literal-only host block, reqwest redirect Policy::limited at input_files.rs:103 so redirects are not re-checked, no DNS check); also video.rs:51-84, a third copy of the loader in another module"
 },
 "O3_reason_to_dismiss": "input_file.file_url already has an SSRF guard (reject_private_host, input_files.rs:132-164) and belongs to the file-attachment feature rather than image_url, so a solver can call it 'already protected' and leave it alone, or copy its literal-only check into parse_image_url, which still lets DNS names and redirects through.",
 "O4_distance": {
  "files": 4,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The same loaders must keep reading local paths and file:// URLs for trusted callers (CLI interactive mode, library users) and must keep accepting data: URLs and public http(s) URLs from server requests. Removing file support from parse_image_url breaks the CLI and the project's own test, which loads a relative path and a file:// URL.",
  "where": "mistralrs-server-core/src/util.rs:240-249; mistralrs-cli/src/commands/run/interactive.rs:329,345,361; mistralrs-server-core/src/util.rs:290-298"
 },
 "O6_input_shapes": [
  "bare relative or absolute filesystem path (no scheme), accepted via File::open probe (util.rs:48)",
  "file:// URL",
  "http/https URL with literal private/loopback/link-local IPv4 or IPv6, including IPv4-mapped IPv6 and special ranges (CGNAT, TEST-NET, 240/4)",
  "hostname such as localhost, *.localhost, *.local, or a hostname that resolves to a private address (DNS check, then pinned resolve_to_addrs)",
  "http redirect to a private host or a non-http scheme (redirects handled manually and re-validated each hop)",
  "data: URL (still allowed, now size-limited)",
  "the same shapes for image_url, audio_url, video_url, and Responses input_file.file_url"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "Media URLs are extracted inline by the request parser (chat_completion.rs:729-770; Anthropic source.into_url at anthropic.rs:746; Responses image_url at responses.rs:153). No schema, serializer or cache produces the dangerous state.",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "Python binding chat request: a separate sync copy of parse_image_url/audio/video that accepts bare paths, file:// and an unrestricted reqwest::blocking::get",
   "where": "mistralrs-pyo3/src/util.rs:201-251",
   "reason_to_dismiss": "An in-process library whose caller is trusted, the same as the fix's own Local policy. The advisory is about the unauthenticated HTTP server.",
   "distance": "different crate (mistralrs-pyo3), different file, sync rather than async",
   "present_in_latest": "yes",
   "latest_where": "latest/mistralrs-pyo3/src/util.rs:201"
  },
  {
   "route": "Python binding audio and video loaders (same unguarded logic), called from the pyo3 chat paths at lib.rs:1240,1246 and 2185,2191",
   "where": "mistralrs-pyo3/src/util.rs:255-305",
   "reason_to_dismiss": "Same as above: library API, trusted caller.",
   "distance": "different crate",
   "present_in_latest": "yes",
   "latest_where": "latest/mistralrs-pyo3/src/util.rs:255"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "mistralrs-server-core/src/anthropic.rs:746",
   "sibling": "Anthropic image source of type url could be fetched directly in the Anthropic adapter instead of being converted into an image_url part",
   "why_realistic": "An adapter author could resolve the Anthropic 'url' source eagerly with reqwest::get to validate it, which bypasses parse_request's server policy."
  },
  {
   "where": "mistralrs-server-core/src/responses.rs:153",
   "sibling": "Responses input_image with image_url could be pre-fetched or validated in responses.rs with the public util::parse_image_url (Local policy)",
   "why_realistic": "util::parse_image_url is the documented public helper, so a maintainer reusing it in another handler would silently get the Local policy."
  },
  {
   "where": "mistralrs-server-core/src/chat_completion.rs:771-792",
   "sibling": "a file part with a path-like file_url or file_data path resolved through the Local loader",
   "why_realistic": "input_file and image share the same parse loop, and a 'support local file for input_file' convenience is plausible."
  }
 ],
 "O9_family": "SSRF plus arbitrary local file read through an untrusted media source URL or path (CWE-918, CWE-73)",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust",
  "toolchain": "cargo (large workspace: candle-based mistralrs-core plus server-core, cli, pyo3 and others)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "mistralrs-server-core/src/util.rs:229-300 test_parse_image_url (needs network for rust-lang.org; local-path, file:// and data: cases are offline); input_files.rs tests; the fix adds media_source, util, video and input_files unit tests. Rejection behaviour is testable offline with literal IPs, localhost and local paths."
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "mistralrs-server-core/src/{chat_completion.rs,util.rs,video.rs,input_files.rs,lib.rs,media_source.rs(new)}",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Copy input_files.rs reject_private_host into parse_image_url and drop the file branch. This misses audio/video (video.rs), hostnames resolving to private IPs, redirects, and IPv4-mapped IPv6, and breaks CLI/local-path use."
 },
 "out_of_scope_notes": [
  "mistralrs-core/src/pipeline/amoe.rs:424-440 AnyMoE training dataset image loader fetches http or reads files from operator config; operator-trusted, not this advisory.",
  "The fix also adds byte limits on media and data: URLs (resource limits, fix.diff:466-506); not counted as the trust decision.",
  "mistralrs-server-core/src/skills.rs:320 fs::read of skill metadata; unrelated feature, not examined."
 ],
 "unverified": [
  "Pinned commit hash not given (parent_commit null); assumed to be the tree in hosts/21576/repo.",
  "Repo size in MB not measured (no shell); giant_repo/tiny_repo not assessed, but this is a multi-crate workspace, clearly over 5 MB.",
  "Did not confirm that /v1/messages/count_tokens (anthropic.rs:1565) actually loads media inside parse_request rather than short-circuiting; assumed, since it calls the same parse_request.",
  "MCP server chat tool (mcp_server.rs:216) is counted as an entry point; whether the MCP server is enabled by default was not checked.",
  "O8 pyo3 routes are arguably by design (trusted in-process caller, matching the fix's Local policy). As Pattern B they would be hard to justify as fair hidden tests, so pattern_fit is A only.",
  "Whether the build needs a GPU was not checked; candle supports CPU, and the affected server-core code has no GPU dependency in the paths read.",
  "Recall risk estimated without a search: GHSA published 2026-09-10."
 ]
}
  ```
- Published fix sites:   - mistralrs-server-core/src/chat_completion.rs:931 — entry point: POST /v1/chat/completions, /v1/responses, /v1/messages, /v1/messages/count_tokens, MCP chat tool (all via chat_completion::parse_request) [HTTP request parser (call site switched to the server-policy loader for images)]
  - mistralrs-server-core/src/chat_completion.rs:940 — entry point: same parse_request routes, audio_url parts [HTTP request parser (audio call site)]
  - mistralrs-server-core/src/chat_completion.rs:949 — entry point: same parse_request routes, video_url parts [HTTP request parser (video call site)]
  - mistralrs-server-core/src/util.rs:45 — entry point: public API mistralrs_server_core::util::parse_image_url (also CLI interactive mode, mistralrs-cli/src/commands/run/interactive.rs:329) [shared media loader / lower-level public API (kept Local policy, server variant added)]
  - mistralrs-server-core/src/util.rs:91 — entry point: public API util::parse_audio_url (CLI interactive.rs:345) [shared media loader, audio variant]
  - mistralrs-server-core/src/video.rs:51 — entry point: public API video::parse_video_url (CLI interactive.rs:361) [separate video module loader (second copy of the same loading logic)]
  - mistralrs-server-core/src/input_files.rs:94 — entry point: POST /v1/responses input_file.file_url (chat completions rejects file_url, chat_completion.rs:785-791) via resolve_input_file, chat_completion.rs:837 [neighbouring feature (input file attachment) with its own pre-existing literal-host guard]
  - mistralrs-server-core/src/input_files.rs:74 — entry point: input_file.file_data on the same routes [size limit on decode (resource limit, not the trust decision)]
  - fix.diff:272-618 — entry point: new crate-private module media_source.rs (policy enum, DNS-resolve-then-pin, manual redirect re-validation, is_global_ip) [new shared guard module]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

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

## Environment (`tasks/mistral.rs-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/mistral.rs-mm/instruction.md`)
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

## Tests (`tasks/mistral.rs-mm/tests/`)
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
- **Wrong-fix patches** go in `build/mistral.rs-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/mistral.rs-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/mistral.rs-mm/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/mistral.rs-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py mistral.rs-mm --only static
python3 -I builder/gate.py mistral.rs-mm --only nop
python3 -I builder/gate.py mistral.rs-mm --only oracle
python3 -I builder/gate.py mistral.rs-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/mistral.rs-mm/`;
  - edit only `tasks/mistral.rs-mm/`, `build/mistral.rs-mm/` and, for pattern B, the register;
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
