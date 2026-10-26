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

Project root: `/home/mara/cwe-bench`. Task: `n8n-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2X35-3FW4-9JR4", "CVE-2026-72766"]; n8n-io/n8n; type confusion leading to local file read / SSRF via library content-object resolution (CWE-843 -> CWE-200/CWE-918)
- Pinned (vulnerable) commit: parent of f69dfc6dd2178a14ea1624d2e1d403c2e755042f (hash not recorded in inputs; repo version 2.32.0). Published fix: f69dfc6dd2178a14ea1624d2e1d403c2e755042f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "7663",
 "advisory_ids": [
  "GHSA-2X35-3FW4-9JR4",
  "CVE-2026-72766"
 ],
 "repo": "n8n-io/n8n",
 "pinned_commit": "parent of f69dfc6dd2178a14ea1624d2e1d403c2e755042f (hash not recorded in inputs; repo version 2.32.0)",
 "fix_commits": [
  "f69dfc6dd2178a14ea1624d2e1d403c2e755042f"
 ],
 "trust_decision": {
  "summary": "Node parameters typed as strings (text/html, also address fields) are passed unchecked into nodemailer mail options, where an object value is treated as a content object ({path}/{href}) that nodemailer resolves from the local filesystem or a URL; the decision of whether workflow-supplied message content may name files/URLs is made (not at all) in the Send Email node before transporter.sendMail / createTransport.",
  "evidence": [
   "packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:158-159",
   "packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:184",
   "packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:215-221",
   "packages/nodes-base/nodes/EmailSend/v2/utils.ts:48",
   "fix.diff:4201-4209",
   "fix.diff:4345-4348"
  ]
 },
 "landing_point": {
  "where": "packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:215-221",
  "why": "Advisory names the Send Email node; the current (v2) send operation is where text/html are read with getNodeParameter and copied into mailOptions without type coercion."
 },
 "fix_sites": [
  {
   "where": "packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:198-221",
   "entry_point": "Workflow execution of Send Email node v2+, operation 'send' (workflow run via editor/REST/webhook)",
   "module_kind": "node operation handler (primary)"
  },
  {
   "where": "packages/nodes-base/nodes/EmailSend/v2/utils.ts:48",
   "entry_point": "configureTransport, shared by v2 send, v2 sendAndWait and SMTP credential test",
   "module_kind": "shared transport factory (lower-level helper)"
  },
  {
   "where": "packages/nodes-base/nodes/EmailSend/v2/sendAndWait.operation.ts:28-29",
   "entry_point": "Workflow execution of Send Email node v2, operation 'sendAndWait'",
   "module_kind": "second operation in same node (address fields only)"
  },
  {
   "where": "packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:153-195",
   "entry_point": "Workflow execution of Send Email node typeVersion 1 (legacy versioned node)",
   "module_kind": "second implementation / legacy version"
  },
  {
   "where": "fix.diff:4195-4209",
   "entry_point": "new helper packages/nodes-base/nodes/EmailSend/utils.ts toMailString used by all above",
   "module_kind": "new shared coercion helper"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "legacy_path",
  "where": "packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:153-195 (v1 node builds its own createTransport at :184, not via v2/utils.ts configureTransport)"
 },
 "O3_reason_to_dismiss": "EmailSend v1 is a superseded node version with its own transport construction; a solver fixing v2 send.operation.ts/configureTransport can argue legacy v1 is not the reported node and is untouched by the shared helper.",
 "O4_distance": {
  "files": 5,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Binary attachments (including inline cid attachments) are passed as content Buffers and must still be sent; v2 appends attribution HTML/text to the body; an over-broad fix (rejecting objects for attachments, stripping attachments, or refusing non-plain-string bodies such as numbers) would break these.",
  "where": "packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:223-259; packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:198-213"
 },
 "O6_input_shapes": [
  "object content value for text/html (e.g. {path} or {href}) -> JSON string (fix.diff:4071-4072, fix.diff:4208)",
  "array value for text/html -> JSON string (fix.diff:4112-4113, fix.diff:4125-4126)",
  "number/boolean/bigint -> toString (fix.diff:4204-4206)",
  "null/undefined -> undefined (fix.diff:4202)",
  "address-like fields from/to/cc/bcc/replyTo, including values nested under options (fix.diff:4233-4242, fix.diff:4282-4284)",
  "transport-level defence: disableFileAccess/disableUrlAccess on createTransport defaults and per-message in v1 (fix.diff:4251-4253, fix.diff:4345-4348)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "Values originate from expression resolution in getNodeParameter (packages/workflow), which can yield objects for string-typed parameters; the fix does not touch it and coerces at the node handler.",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "Gmail node v1 message send/reply and draft create pass uncoerced 'message' and 'htmlMessage' parameters as text/html into nodemailer MailComposer, which resolves content objects without disableFileAccess/disableUrlAccess",
   "where": "packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:319-331; packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:430-445; packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:650-663; sink packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:209-250",
   "reason_to_dismiss": "Different node (Gmail API, not SMTP / Send Email), a legacy v1 version (default is 2.2 at packages/nodes-base/nodes/Google/Gmail/Gmail.node.ts:16), and v2 already String()-coerces the body at packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:432, so it looks already handled.",
   "distance": "Different node directory (nodes/Google/Gmail vs nodes/EmailSend), same nodes-base package; uses MailComposer from nodemailer/lib/mail-composer rather than createTransport.",
   "present_in_latest": "no",
   "latest_where": "latest/packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:243-244 (disableFileAccess/disableUrlAccess now set in encodeEmail; v1 still uncoerced at latest/packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:319)"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:245-259",
   "sibling": "An attachment option that accepts a per-attachment 'path'/'href' or a content value taken from a node parameter instead of the binary buffer",
   "why_realistic": "nodemailer natively supports path/href attachments, and a maintainer adding 'attach file by path/URL' would pass it straight through, bypassing toMailString."
  },
  {
   "where": "packages/nodes-base/nodes/EmailSend/v2/sendAndWait.operation.ts:46-51",
   "sibling": "A free-form text alternative/body option on sendAndWait passed raw into mailOptions",
   "why_realistic": "Send-and-wait builds its own mailOptions separate from send.operation.ts; a plain-text fallback option would be a natural feature addition."
  },
  {
   "where": "packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:211-226",
   "sibling": "Already present: encodeEmail builds MailComposer options without file/URL restrictions",
   "why_realistic": "Separate MIME-building helper for an API-based node; maintainers think of it as 'encoding', not as a mail transport."
  }
 ],
 "O9_family": "type confusion leading to local file read / SSRF via library content-object resolution (CWE-843 -> CWE-200/CWE-918)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node >=22.22, pnpm 10.32.1 monorepo (turbo), vitest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "packages/nodes-base/nodes/EmailSend/test/v1/EmailSendV1.node.test.ts, packages/nodes-base/nodes/EmailSend/test/v2/send.operation.test.ts, packages/nodes-base/nodes/EmailSend/test/v2/sendAndWait.operation.test.ts (nodemailer mocked); Gmail tests under packages/nodes-base/nodes/Google/Gmail/test"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/nodes-base/nodes/EmailSend/utils.ts (new), packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts, packages/nodes-base/nodes/EmailSend/v2/send.operation.ts, packages/nodes-base/nodes/EmailSend/v2/sendAndWait.operation.ts, packages/nodes-base/nodes/EmailSend/v2/utils.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Wrap text/html in String() in v2 send.operation.ts only, leaving v1 (own createTransport) and the Gmail MailComposer path unrestricted."
 },
 "out_of_scope_notes": [
  "Fix commit f69dfc6 is a bundled security release (~34 files): Git, Snowflake, PostgresTrigger, EditImage, MCP, ToolHttpRequest, LLM nodes, token-exchange, task-runner, lodash patch etc. belong to sibling advisories; only EmailSend changes are this advisory's.",
  "packages/cli/src/user-management/email/node-mailer.ts:40 createTransport without restrictions, but content comes from server templates, not workflow parameters.",
  "packages/nodes-base/nodes/Brevo/GenericFunctions.ts:134-135 uses MailComposer only for address parsing (compile().getAddresses(), no build); latest adds disableFileAccess defensively."
 ],
 "unverified": [
  "Pinned commit hash not provided (parent_commit null); only fix commit known.",
  "Repo size in MB not measured (~57k files).",
  "Assumed nodemailer MailComposer honours disableFileAccess/disableUrlAccess passed in mail data and otherwise resolves {path}/{href} content for text/html; library source not read.",
  "Assumed getNodeParameter can return an object for string-typed 'message'/'htmlMessage' in Gmail v1 just as it does for EmailSend (same mechanism as the advisory); not traced through packages/workflow.",
  "Whether the Gmail encodeEmail hardening in latest came from a separate advisory is unknown.",
  "Recall risk estimated; public write-up extent not checked (no network)."
 ]
}
  ```
- Published fix sites:   - packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:198-221 — entry point: Workflow execution of Send Email node v2+, operation 'send' (workflow run via editor/REST/webhook) [node operation handler (primary)]
  - packages/nodes-base/nodes/EmailSend/v2/utils.ts:48 — entry point: configureTransport, shared by v2 send, v2 sendAndWait and SMTP credential test [shared transport factory (lower-level helper)]
  - packages/nodes-base/nodes/EmailSend/v2/sendAndWait.operation.ts:28-29 — entry point: Workflow execution of Send Email node v2, operation 'sendAndWait' [second operation in same node (address fields only)]
  - packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:153-195 — entry point: Workflow execution of Send Email node typeVersion 1 (legacy versioned node) [second implementation / legacy version]
  - fix.diff:4195-4209 — entry point: new helper packages/nodes-base/nodes/EmailSend/utils.ts toMailString used by all above [new shared coercion helper]
- Uncovered routes to confirm (pattern B):   - packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:319-331; packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:430-445; packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:650-663; sink packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:209-250 — Gmail node v1 message send/reply and draft create pass uncoerced 'message' and 'htmlMessage' parameters as text/html into nodemailer MailComposer, which resolves content objects without disableFileAccess/disableUrlAccess (reason to dismiss: Different node (Gmail API, not SMTP / Send Email), a legacy v1 version (default is 2.2 at packages/nodes-base/nodes/Google/Gmail/Gmail.node.ts:16), and v2 already String()-coerces the body at packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:432, so it looks already handled.; still in latest: no)
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

## Environment (`tasks/n8n-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/n8n-ds/instruction.md`)
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

## Tests (`tasks/n8n-ds/tests/`)
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
- **Wrong-fix patches** go in `build/n8n-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/n8n-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/n8n-ds/manifest.json`:**
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

**Also in `build/n8n-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py n8n-ds --only static
python3 -I builder/gate.py n8n-ds --only nop
python3 -I builder/gate.py n8n-ds --only oracle
python3 -I builder/gate.py n8n-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/n8n-ds/`;
  - edit only `tasks/n8n-ds/`, `build/n8n-ds/` and, for pattern B, the register;
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
