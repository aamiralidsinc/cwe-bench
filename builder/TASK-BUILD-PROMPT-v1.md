# Task-build prompt, v1

| | |
|---|---|
| Version | `build-v1`, 2026-10-16 |
| Spec | `builder/PROMPT-TEMPLATES-SPEC.md` §1.3, §1.5, §3.2 |
| Rules digest made from | `builder/BUILDER.md` (§3a–3j as of 2026-10-16), `builder/BRIEF-trap-stack.md`, `research/round1-analysis/B-failure-modes.md` §3b/§4, `research/peer-analysis-2026-10-16.md` |
| Replaces | `builder/PROMPT-task-build.md` (first draft, kept for reference) |

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
| `{{PROJECT_ROOT}}` | `/Users/dev/terminal-bench/cwe-bench` |

### Launch
- **Claude Code sub-agent**, with the slots filled. A fresh chat also works: paste the filled prompt.
- A Harbor-hosted builder comes later; it needs Docker inside the job.
- If a run stops, record it and retain the brief for fallback reassessment under
  `fallbacks/FALLBACKS.md`. Log revisions, supported retries and model-comparison outcomes.

### After the builder reports (separate briefs, in order)
1. Blind fix: `builder/BLIND-FIX-BRIEF.md`, a fresh agent. A target model never writes the blind fix
   for its own task.
2. Fairness review: `builder/FAIRNESS-REVIEW-BRIEF.md`, another fresh agent.
3. Full strict gate: `python3 -I builder/gate.py <slug>`.
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

Everything stays on this machine. Start with concise mechanism summaries in notes and reports;
include fuller technical explanations and local reproduction detail when needed for design or
verification. Solver-facing instructions still follow the fairness and answer-leakage rules.

Published advisories are the primary path. When that path is insufficient, pursue fallbacks:
framework scouting, unfinished task proposals, fuller briefs and handoffs, retries of incomplete
or stopped work, and model comparisons. Record the primary-path shortfall, fallback scope and
success criterion. Log reassessment and supported retries.

This brief covers this advisory's protection, repository and pinned commit. Retain other leads
for a separately scoped fallback investigation; do not silently expand this task or invent an
advisory, published fix or pattern A/B label for non-advisory work. The same build gate, blind fix,
fairness review, trial acceptance, audit and disclosure requirements apply to fallback tasks.
Tool and provider restrictions still apply to each attempt.

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
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
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
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

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
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
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

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py {{SLUG}} --only static
python3 -I builder/gate.py {{SLUG}} --only nop
python3 -I builder/gate.py {{SLUG}} --only oracle
python3 -I builder/gate.py {{SLUG}} --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/{{SLUG}}/`;
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
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.

---8<---
