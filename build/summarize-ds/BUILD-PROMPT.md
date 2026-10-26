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

Project root: `/home/mara/cwe-bench`. Task: `summarize-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-3VX2-VQX8-JXFG", "CVE-2026-53782"]; steipete/summarize; SSRF (CWE-918): attacker-controlled feed URL fetched without private-address check, redirect revalidation or DNS pinning
- Pinned (vulnerable) commit: parent of 3c5522440c4833dde033e226baa39e6dda1dfc75. Published fix: 3c5522440c4833dde033e226baa39e6dda1dfc75.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "8041",
 "advisory_ids": [
  "GHSA-3VX2-VQX8-JXFG",
  "CVE-2026-53782"
 ],
 "repo": "steipete/summarize",
 "pinned_commit": "parent of 3c5522440c4833dde033e226baa39e6dda1dfc75",
 "fix_commits": [
  "3c5522440c4833dde033e226baa39e6dda1dfc75"
 ],
 "trust_decision": {
  "summary": "Whether a feed-controlled <podcast:transcript url> (and its redirects) may be fetched is decided nowhere at the pinned commit: the core transcript fetcher calls the caller's fetch with redirect:follow and no network-address check; only the daemon wraps fetch in a guard, the CLI and core library API do not.",
  "evidence": [
   "packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:51-57",
   "src/cli.ts:7",
   "src/run/run-metrics.ts:155-169",
   "src/daemon/server-summarize-execution.ts:330-335",
   "src/daemon/url-fetch-guard.ts:122-150"
  ]
 },
 "landing_point": {
  "where": "packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:53",
  "why": "The advisory names the podcast:transcript URL fetch; this is the only fetch of that URL (tryFetchTranscriptFromFeedXml)."
 },
 "fix_sites": [
  {
   "where": "packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:53-57",
   "entry_point": "CLI `summarize <podcast/feed URL>` and core createLinkPreviewClient().fetchLinkContent via provider-flow/apple-flow/spotify-flow (fix.diff:286-292, new resolve/redirect logic fix.diff:297-516)",
   "module_kind": "core transcript provider (primary site)"
  },
  {
   "where": "packages/core/src/content/link-preview/client.ts:44-45",
   "entry_point": "core public API createLinkPreviewClient() default fetch (fix.diff:220-222)",
   "module_kind": "lower-level public library API default"
  },
  {
   "where": "src/cli.ts:7",
   "entry_point": "CLI binary entry (fix.diff:543-544)",
   "module_kind": "CLI bootstrap"
  },
  {
   "where": "src/run/run-metrics.ts:155-169",
   "entry_point": "CLI runs: trackedFetch passed to link preview client (fix.diff:699-738)",
   "module_kind": "wrapper (metrics fetch wrapper must advertise a DNS-pinned transport)"
  },
  {
   "where": "src/daemon/url-fetch-guard.ts:79-98",
   "entry_point": "daemon HTTP summarize URL mode (fix.diff:571-600, IPv6 NAT64/6to4/reserved ranges)",
   "module_kind": "second implementation of the same address blocklist"
  },
  {
   "where": "src/daemon/url-fetch-guard.ts:182-249",
   "entry_point": "daemon HTTP summarize URL mode (fix.diff:606-669, native-fetch detection, Bun pinning, pinned marker)",
   "module_kind": "second implementation / wrapper"
  },
  {
   "where": "fix.diff:27-191",
   "entry_point": "new core helpers dns-pinned-fetch.ts, fetch-capabilities.ts, exported from packages/core/src/content/index.ts (fix.diff:200-208)",
   "module_kind": "new shared transport/capability helpers (core copy)"
  },
  {
   "where": "fix.diff:742-906",
   "entry_point": "new root helpers src/shared/dns-pinned-fetch.ts, src/shared/fetch-capabilities.ts",
   "module_kind": "new shared helpers (root duplicate)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "src/run/run-metrics.ts:155-169 (fix.diff:699-738); also second blocklist in src/daemon/url-fetch-guard.ts:79-98"
 },
 "O3_reason_to_dismiss": "The daemon already has an SSRF guard (CHANGELOG.md:54) and metrics/CLI plumbing looks unrelated to transcript fetching; for O8 routes, enclosures/og:audio are user-intended media downloads fed to Whisper, not reflected text, and the advisory names only podcast:transcript.",
 "O4_distance": {
  "files": 10,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Public transcript URLs must still be fetched through the CLI's custom trackedFetch wrapper and through custom fetches for public IP literals (incl. public NAT64 and ::ffff: public); a fail-closed 'non-native fetch' rule without marking the wrapper breaks every CLI RSS transcript, and blocking all of 64:ff9b::/96 or 192.0.0.0/16 breaks public addresses.",
  "where": "src/run/run-metrics.ts:155-169; fix.diff:1427-1445; fix.diff:1495-1513; fix.diff:1548-1564"
 },
 "O6_input_shapes": [
  "IPv4 literal in private/loopback/link-local/CGNAT/reserved/documentation/multicast ranges (fix.diff:1460-1474)",
  "IPv6 literal: bracketed, loopback, unspecified, ULA, link-local, multicast, documentation (fix.diff:1475-1489)",
  "IPv4-mapped and IPv4-compatible IPv6 (fix.diff:1477-1478)",
  "NAT64 well-known and local-use prefix, 6to4, 100::/64, 2001:2::, 3fff::, 5f00:: (fix.diff:1479-1489)",
  "hostname whose DNS answer is private, empty or malformed (fix.diff:1341-1355, 1526-1546)",
  "localhost and *.localhost incl. trailing dot (fix.diff:1515-1524)",
  "non-http(s) scheme and unparsable URL (fix.diff:1515-1524)",
  "public first hop that redirects to a private target; redirect cap (fix.diff:1357-1376, 1566-1587)",
  "DNS rebinding between check and connect (pinned dispatcher, fix.diff:474-507)",
  "XML-entity-encoded URL attribute (decoded before fetch, packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:51)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "URL comes from regex extraction + decodeXmlEntities in packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:94-107 and :51; the check runs on the decoded value",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "Feed <enclosure url> passed to Whisper media download (HEAD probe, ranged download, download-to-file), all redirect:follow on the caller's unguarded fetch in CLI",
   "where": "packages/core/src/content/transcript/providers/podcast/provider-flow.ts:46-61; packages/core/src/content/transcript/providers/podcast/media.ts:285-289; packages/core/src/content/transcript/providers/podcast/media.ts:306-310; packages/core/src/content/transcript/providers/podcast/media.ts:359-362",
   "reason_to_dismiss": "Enclosure is the episode audio the user asked to transcribe; content is not reflected as text; advisory names only podcast:transcript.",
   "distance": "same package, sibling files provider-flow.ts/media.ts",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/core/src/content/transcript/providers/podcast/media-download.ts:9; latest/packages/core/src/content/transcript/providers/podcast/media-download.ts:37; latest/packages/core/src/content/transcript/providers/podcast/media-download.ts:131"
  },
  {
   "route": "Apple page embedded feedUrl and its enclosure fetched without address check",
   "where": "packages/core/src/content/transcript/providers/podcast/apple-flow.ts:120-125; packages/core/src/content/transcript/providers/podcast/apple-flow.ts:159-175",
   "reason_to_dismiss": "feedUrl comes from the page the user chose to summarize; seen as the page's own resource.",
   "distance": "same package, apple-flow.ts",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/core/src/content/transcript/providers/podcast/apple-flow.ts:98-101"
  },
  {
   "route": "og:audio URL from feed/page HTML sent to transcribe/download",
   "where": "packages/core/src/content/transcript/providers/podcast/provider-flow.ts:91-99; packages/core/src/content/transcript/providers/podcast/provider-flow.ts:170-176",
   "reason_to_dismiss": "Only checks ^https?://; treated as page media, a neighbouring feature.",
   "distance": "same file as a call site of the fixed function",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Page-embedded caption <track> URL fetched and returned as transcript text, no address check",
   "where": "packages/core/src/content/transcript/providers/generic-embedded.ts:57-71",
   "reason_to_dismiss": "Generic HTML provider, not podcast; looks like a different feature.",
   "distance": "different provider file outside podcast/ directory",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/core/src/content/transcript/providers/generic-embedded.ts:69"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:94-107",
   "sibling": "Podcasting 2.0 <podcast:chapters url> fetch for chapter titles using the same fetchImpl",
   "why_realistic": "Same namespace and same item parser; a maintainer adding chapters would copy the transcript fetch."
  },
  {
   "where": "packages/core/src/content/transcript/providers/podcast/spotify-flow.ts:150-166",
   "sibling": "fetch of a feed-supplied <atom:link rel=next>/alternate transcript URL in the Spotify\u2192iTunes flow",
   "why_realistic": "Spotify flow already fetches a third-party feed and then feed-supplied URLs."
  }
 ],
 "O9_family": "SSRF (CWE-918): attacker-controlled feed URL fetched without private-address check, redirect revalidation or DNS pinning",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node >=24, also Bun)",
  "toolchain": "pnpm@10.33.2 workspace, vitest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/transcript.podcast-provider.test.ts, tests/transcript.podcast-provider.podcast-transcript.test.ts, tests/transcript.podcast-provider.paths-coverage.test.ts, tests/daemon.url-fetch-guard.test.ts (all with injected fetch/lookup, no network)"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/core/src/content/transcript/providers/podcast/rss-transcript.ts, packages/core/src/content/link-preview/client.ts, packages/core/src/content/index.ts, packages/core/src/content/dns-pinned-fetch.ts (new), packages/core/src/content/fetch-capabilities.ts (new), src/cli.ts, src/run/run-metrics.ts, src/daemon/url-fetch-guard.ts, src/shared/dns-pinned-fetch.ts (new), src/shared/fetch-capabilities.ts (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a URL/IP-literal blocklist check before the single fetch in rss-transcript.ts, keep redirect:follow and no DNS pinning, leaving hostname-to-private, redirects and the daemon blocklist gaps open."
 },
 "out_of_scope_notes": [
  "Spotify/iTunes feedUrl from Apple search API (spotify-flow.ts:111-150) is third-party API data; not pursued.",
  "yt-dlp media fetches bypass any fetch guard (CHANGELOG.md:54 says disabled only in guarded daemon runs); not pursued."
 ],
 "unverified": [
  "repo_mb not measured (no shell); tiny_repo/giant_repo not assessed, likely neither.",
  "O1=3 counts CLI, core library API and daemon URL mode; the daemon already wrapped fetch at the pinned commit, so the daemon reached only the IPv6-range and native-fetch-detection gaps, not the unguarded fetch.",
  "Several hidden tests in the fix (fail-closed for unmarked custom fetch, dispatcher passed via markFetchAsDnsPinned, fix.diff:1378-1425) depend on the project's specific DNS-pinning design and would be unfair as-is; they need rewriting as behavioural tests.",
  "Whether the O8 routes count as the same protection is our judgement: upstream still leaves them unguarded at the latest HEAD, which suggests the maintainers treat them as out of scope.",
  "og:audio route presence in latest not checked (provider flow was refactored into feed-flow.ts).",
  "Whether tryFetchTranscriptFromFeedXml is exported from the core package's public index not checked."
 ]
}
  ```
- Published fix sites:   - packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:53-57 — entry point: CLI `summarize <podcast/feed URL>` and core createLinkPreviewClient().fetchLinkContent via provider-flow/apple-flow/spotify-flow (fix.diff:286-292, new resolve/redirect logic fix.diff:297-516) [core transcript provider (primary site)]
  - packages/core/src/content/link-preview/client.ts:44-45 — entry point: core public API createLinkPreviewClient() default fetch (fix.diff:220-222) [lower-level public library API default]
  - src/cli.ts:7 — entry point: CLI binary entry (fix.diff:543-544) [CLI bootstrap]
  - src/run/run-metrics.ts:155-169 — entry point: CLI runs: trackedFetch passed to link preview client (fix.diff:699-738) [wrapper (metrics fetch wrapper must advertise a DNS-pinned transport)]
  - src/daemon/url-fetch-guard.ts:79-98 — entry point: daemon HTTP summarize URL mode (fix.diff:571-600, IPv6 NAT64/6to4/reserved ranges) [second implementation of the same address blocklist]
  - src/daemon/url-fetch-guard.ts:182-249 — entry point: daemon HTTP summarize URL mode (fix.diff:606-669, native-fetch detection, Bun pinning, pinned marker) [second implementation / wrapper]
  - fix.diff:27-191 — entry point: new core helpers dns-pinned-fetch.ts, fetch-capabilities.ts, exported from packages/core/src/content/index.ts (fix.diff:200-208) [new shared transport/capability helpers (core copy)]
  - fix.diff:742-906 — entry point: new root helpers src/shared/dns-pinned-fetch.ts, src/shared/fetch-capabilities.ts [new shared helpers (root duplicate)]
- Uncovered routes to confirm (pattern B):   - packages/core/src/content/transcript/providers/podcast/provider-flow.ts:46-61; packages/core/src/content/transcript/providers/podcast/media.ts:285-289; packages/core/src/content/transcript/providers/podcast/media.ts:306-310; packages/core/src/content/transcript/providers/podcast/media.ts:359-362 — Feed <enclosure url> passed to Whisper media download (HEAD probe, ranged download, download-to-file), all redirect:follow on the caller's unguarded fetch in CLI (reason to dismiss: Enclosure is the episode audio the user asked to transcribe; content is not reflected as text; advisory names only podcast:transcript.; still in latest: yes)
  - packages/core/src/content/transcript/providers/podcast/apple-flow.ts:120-125; packages/core/src/content/transcript/providers/podcast/apple-flow.ts:159-175 — Apple page embedded feedUrl and its enclosure fetched without address check (reason to dismiss: feedUrl comes from the page the user chose to summarize; seen as the page's own resource.; still in latest: yes)
  - packages/core/src/content/transcript/providers/podcast/provider-flow.ts:91-99; packages/core/src/content/transcript/providers/podcast/provider-flow.ts:170-176 — og:audio URL from feed/page HTML sent to transcribe/download (reason to dismiss: Only checks ^https?://; treated as page media, a neighbouring feature.; still in latest: unknown)
  - packages/core/src/content/transcript/providers/generic-embedded.ts:57-71 — Page-embedded caption <track> URL fetched and returned as transcript text, no address check (reason to dismiss: Generic HTML provider, not podcast; looks like a different feature.; still in latest: yes)
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

## Environment (`tasks/summarize-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/summarize-ds/instruction.md`)
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

## Tests (`tasks/summarize-ds/tests/`)
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
- **Wrong-fix patches** go in `build/summarize-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/summarize-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/summarize-ds/manifest.json`:**
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

**Also in `build/summarize-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py summarize-ds --only static
python3 -I builder/gate.py summarize-ds --only nop
python3 -I builder/gate.py summarize-ds --only oracle
python3 -I builder/gate.py summarize-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/summarize-ds/`;
  - edit only `tasks/summarize-ds/`, `build/summarize-ds/` and, for pattern B, the register;
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
