# Task-build prompt, v1

> **FORMAT (2026-10-21): Frontier-SWE delivery format.** Fill the skeletons in `common/builder/templates/` and follow `common/builder/FRONTIER-CONFORMANCE-SPEC.md`. The gate enforces it via `common/builder/conformance_check.py`, so a non-conforming task fails. Where any guidance below predates this and says `/app`, "delete `.git`", a model-host **allowlist**, or "do not modify/add tests", it is SUPERSEDED: use `/workspace`; keep the fresh one-commit git baseline (do not delete it); `[agent]` and `[verifier]` are `network_mode = "no-network"` with NO allowlist (the model host is allowed at run time via `--allow-agent-host`); and `instruction.md` must not mention tests or grading.


| | |
|---|---|
| Version | `build-v1`, 2026-10-16 |
| Spec | `common/builder/PROMPT-TEMPLATES-SPEC.md` §1.3, §1.5, §3.2 |
| Rules digest made from | `common/builder/BUILDER.md` (§3a–3j as of 2026-10-16), `common/builder/BRIEF-trap-stack.md`, `docs/research/round1-analysis/B-failure-modes.md` §3b/§4, `docs/research/peer-analysis-2026-10-16.md` |
| Replaces | `common/archive/old-prompts/PROMPT-task-build.md` (first draft, kept for reference) |

`BUILDER.md` stays the authority. When it changes, regenerate the shared core and bump the version.

## Operator part (never sent)

### Per-task slots
| Slot | Fill with |
|---|---|
| `{{SLUG}}` | task directory name |
| `{{PATTERN}}` | `A`, `B` or `A+B` (from the screener's `pattern_fit`, chosen by the lead) |
| `{{TRACK}}` | `mined`, `stacking` or `injected` |
| `{{ADVISORY}}` | advisory ids, repo, CWE, one-line summary |
| `{{VULN_COMMIT}}` / `{{FIX_COMMITS}}` | the pinned commit and the published fix commit(s) |
| `{{SCREEN_RECORD}}` | the screener's JSON for this host (`sourcer/review/screener-v1/<entry_id>.json`) |
| `{{FIX_SITES}}` | the published fix's sites and entry points (screener `fix_sites`, O1–O7) |
| `{{UNCOVERED_ROUTES}}` | pattern B only: the screener's O8 leads, to be confirmed; `none` otherwise |
| `{{DESIGN_PLAN}}` | the lead's plan: the main lever; sites, routes and input shapes to test; coupled behaviours; injected siblings, if any, with place and why they are realistic |
| `{{HOST_NOTES}}` | build gotchas, things to avoid, credit lines (e.g. "producer-off-path shape: credit Hadi"); `none` if empty |
| `{{PROJECT_ROOT}}` | the repo root (the folder holding `.cwe-bench-root`); the prepare step fills it |

### Launch
- **Claude Code sub-agent**, with the slots filled. A fresh chat also works: paste the filled prompt.
- A Harbor-hosted builder comes later; it needs Docker inside the job.
- If a run is stopped by a safety check, narrow the prompt, for example by splitting design from
  build. Log the change. Never re-run a stopped prompt on another model.

### After the builder reports (separate briefs, in order)
1. Blind fix: `common/blindfix/BLIND-FIX-BRIEF.md`, a fresh agent. A target model never writes the blind fix
   for its own task.
2. Fairness review: `common/fairness/FAIRNESS-REVIEW-BRIEF.md`, another fresh agent.
3. Full strict gate: `python3 -I common/gate/gate.py <slug>` (the post-build gate, `common/gate/postbuild.sh`; the
   builder runs only static and nop, 2026-10-28).
4. Trials: both models, up to 3 runs each, offline, 2 h limit.
5. Post-run audit of every graded run.
6. Pattern B: check that every route has its row in `build/audit/uncovered-routes.tsv`, with
   `present_in_latest` filled in, before anything is shared outside the project.

### Builder model comparison
| Date | Model | Slug | Gate stages first try | Fairness, first round | Repair rounds | Wall time | Stops |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

### Change log
- build-v1 (2026-10-16): first version, written from the spec.
- 2026-10-28 (pipeline fixes, item 3; no version bump): the builder runs only the static and nop stages (oracle
  and patches are the post-build gate's; local proofs instead); rules on waiting (no `pgrep -f`/`pkill -f`,
  logs under the work folder, nothing left running at the report), target daemons only in Docker, no gate
  limits, no markers or start/end stamps. Eleven builds hit the 5-h limit waiting on gate slots for stages the
  post-build gate repeats; four builders were killed by name-based kills.

---

## The prompt (send everything between the markers)

---8<---

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

Project root: `{{PROJECT_ROOT}}`. Task: `{{SLUG}}`. Pattern: `{{PATTERN}}`. Track: `{{TRACK}}`.

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
- Advisory: {{ADVISORY}}
- Pinned (vulnerable) commit: {{VULN_COMMIT}}. Published fix: {{FIX_COMMITS}}.
- The screener's record (a lead to verify, not a fact):
  ```json
  {{SCREEN_RECORD}}
  ```
- Published fix sites: {{FIX_SITES}}
- Uncovered routes to confirm (pattern B): {{UNCOVERED_ROUTES}}
- Design plan from the lead: {{DESIGN_PLAN}}
- Host notes: {{HOST_NOTES}}

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `{{PROJECT_ROOT}}/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/{{SLUG}}/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/{{SLUG}}/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/{{SLUG}}/tests/`)
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
- **Refusals.** Where a security test drives a hardened function or handler directly (not through an HTTP
  or CLI entry point), a refusal is a secure outcome: use the shared helper from
  `common/builder/templates/support/refusal/` (copy it into `tests/support/`) and pass the product's own
  refusal exceptions. A client error or a declared refusal passes; a 5xx or any other exception still fails.
  Check side effects after every outcome.
- **Stand-ins mirror the real code.** A stub class compiled ahead of the real one declares every public
  member of the real class. A mocked library exports everything the real library offers that a fix may use
  (transactions, constants, error types). A fake network sits below every client: name resolution
  (`dns.lookup` and the resolver bindings) and connections, never `fetch` alone. Never map a host that a
  functional test treats as public to a loopback address.
- **No timing flakiness.** Upstream Hypothesis suites run with `deadline=None` (a conftest profile).
  Wall-clock limits stay far above the reference fix's time under full load.
- **Project tests.** The project's own tests run from copies in `tests/pristine/` at the pinned commit,
  never from the agent's `/workspace`.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged (it counts
  setup errors and a crashed runner as failures). Edit only the marked command lines of `test.sh`, keep its
  agent-kill block and the line that records each group's exit code.
- **Lint before the gate.** Run `python3 -I common/lint/task_lint.py tasks/{{SLUG}}` and fix every
  warning, or say in `notes.md` why it does not apply. The lint never blocks; the fairness review after
  trials still decides.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/{{SLUG}}/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/{{SLUG}}/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/{{SLUG}}/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `{{PATTERN}}`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/{{SLUG}}/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run these two stages yourself, in order, one at a time, from the project root above:
```
python3 -I common/gate/gate.py {{SLUG}} --only static
python3 -I common/gate/gate.py {{SLUG}} --only nop
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

The oracle and patches stages are NOT yours: the post-build gate runs every stage after you report
(the gate refuses them from a builder). Prove them locally instead: apply `solution/` and each
`checks/` patch to a copy of the pinned code in your scratch folder and run the tests there (every
test passes with the reference fix; each patch gives the result its manifest entry expects). Report
those local results as "local", and the static and nop results as the gate's.

**Waiting and processes.**
- Run each stage in the foreground, or start it with its output in
  `~/.tb-graders/cwe/work/{{SLUG}}/logs/<stage>.log` and wait in bounded foreground loops (under 10
  minutes each) for its last line, or with `tail --pid=<the pid you started>`. Never wait with, and
  never kill by, `pgrep -f` or `pkill -f`: the pattern matches its own command line and other jobs'.
  Stop only processes you started, by the pid you recorded.
- Before your final report, nothing of yours may still run: no background task, Monitor, waiter,
  server or container. Stop them, or this session never ends.
- Run the target's daemons, background services, updaters and self-repair routes only inside Docker,
  never on the host: some kill every process on the machine whose name matches theirs.
- Never set `GATE_GLOBAL_SLOTS`, `GATE_PARALLEL` or any other gate limit.
- Never write gate markers (`.sound`, `.unsound`, `.gate_error`, `gate_fingerprint.json`) or
  `start_utc.txt` / `end_utc.txt`: the pipeline writes them.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers or processes you did not start.
- **Files:**
  - scratch work and logs go in `~/.tb-graders/cwe/work/{{SLUG}}/`, never in shared `/tmp` names
    (another builder's log of the same name overwrote one);
  - edit only `tasks/{{SLUG}}/`, `build/{{SLUG}}/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for static and nop, and your local oracle and patch results.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.

---8<---
