# Spec: the shared screener prompt and the shared task-build prompt

Status: specification, 2026-10-16. The prompt files written from it are
`builder/SCREENER-PROMPT-v1.md` and `builder/TASK-BUILD-PROMPT-v1.md`. The first drafts
(`builder/PROMPT-screener.md`, `builder/PROMPT-task-build.md`) are kept for reference only. They do
not meet this spec (see "Why the first drafts miss" at the end of part 1).

**Two patterns, both in scope (user decision, 2026-10-16).** Both go through the screener and the
builder:
- **Pattern A, published scope.** All difficulty comes from the published fix's own sites:
  - several entry points, one in a module that looks out of scope;
  - input-shape variants;
  - a behaviour that must keep working.
  Evidence: the peer hono task (both models 0/3) and nltk (DeepSeek 3/3).
- **Pattern B, uncovered routes.** At the pinned vulnerable commit, the advisory's own protection is
  also missing on routes its published fix did not touch, in unmodified upstream code. The task's
  reference fix covers them too. Evidence: jackson-databind-sib (DeepSeek 0/6) and
  jackson-databind-sib2 (both models 0/3).

Siblings we inject into our own copy can be added to either pattern. Pattern B comes with three
guardrails (§1.5): a scope limit, a disclosure register, and summary-level write-ups.

Sections: 1. Purpose · 2. Sources · 3. Contents.

---

## 1. Purpose

### 1.1 Why two shared, written-once prompts
The user's request (handoff conversation "CWE-bench plan.md handoff analysis", 2026-10-16 17:41 UTC)
calls for two prompts, each written once:
- a **shared screener prompt** "with goals and objectives". It is tried on the available models
  (Fable 5.1, Opus 4.8, DeepSeek V4.1 Flash, MiMo-V2.6-Pro and others), and then run on every new
  batch with the current weights and instructions;
- a **refined task-build template** shared across all tasks, plus a short per-task section.

They solve three problems from 2026-10-16:
1. **Repeated stops by the safety classifier.**
   - Each hand-written brief was a new chance of being stopped. 10 responses were stopped that day:
     porting Hadi's weakness report onto new injected bugs, the jackson type-validator builder, the
     framework scout, the re-screen launch, the handoff file and several planning replies.
   - Briefs that stayed on **published, already-fixed advisories** and on **building the benchmark
     task** went through: round 1, the instruction rewrites, better-auth.
   - What was stopped: open-ended asks to find **new weaknesses across live, widely used
     frameworks** with no advisory as the anchor (the framework scout), and exploit-level detail.
     Pattern B differs in scope: it stays inside one published advisory's own protection, in one
     repo, at one pinned commit. It may still draw stops, so §1.5 limits it and the narrowing rule
     applies.
   - A template fixed once on the framing that works removes this brief-by-brief variance.
2. **Scale.** 100–200 tasks cannot come from a hand-written brief per task. The user's words: "we
   gotta deliver results ... I can't go back to cave man things".
3. **Model portability.** The pipeline will eventually run on DeepSeek or MiMo. The prompts must
   work outside this Claude Code session:
   - as a Harbor job with Claude Code as the harness;
   - as a prompt pasted into a new chat (the user's "prompt.md" idea).

What the templates are **not**: a way past the classifier. Running the same acceptable prompt on
several models to compare quality is fine. Moving a stopped prompt to another model or session is
not. If a template run is stopped, narrow the template.

### 1.2 File 1: the screener prompt
**Job:** judge each published, already-fixed advisory in our index as a **host** for a task, and
record that judgement in a fixed, machine-readable form, so that a script can score and rank
candidates and we know which to build.
- **Screens hosts, not advisories.** Round 1 showed that advisory-level signals did not predict
  difficulty (ρ −0.06). Difficulty comes from properties of the host code and of the published fix:
  - several entry points;
  - a site that looks out of scope;
  - distance from where the report leads;
  - a behaviour next to the sink that must keep working;
  - for pattern B, routes where the advisory's protection is also missing and that the published
    fix left untouched.
- **Written once, rerun many times.** The weights and the current lessons are inputs, never edits to
  the prompt. When we learn something, we update the weights file or the lessons digest, and rerun.
- **Model choice by measurement.** The same prompt runs on each available model, on hosts whose
  outcome we already know. Routine screening then uses the cheapest model whose judgements match the
  reference.
- **Out of scope:**
  - looking beyond the advisory's own protection, or beyond its repo;
  - building tasks;
  - running exploits;
  - running target models.

### 1.3 File 2: the task-build prompt
**Job:** turn ONE screened host into ONE Harbor security-fix task that passes the gate, from one
shared core plus a short per-task section.
- **The shared core** holds what is the same for every task:
  - goal and acceptance rule;
  - design, instruction and test rules;
  - deliverables, gate stages, machine limits and the report format.
- **The per-task section** holds only:
  - slug, advisory, commits and track;
  - the screener's record;
  - the chosen task design;
  - host notes.
- **It covers design and build only.** Blind fix, fairness review, strict gate, trials and per-run
  audits stay separate stages with their own briefs (`builder/NEXT-STEPS.md`, "Process").
- **The same comparison method applies.** Builder models are compared on:
  - whether the gate passes;
  - the fairness verdict;
  - rounds of repair needed;
  - wall time.
- **Material is limited to:**
  - the published advisory and its published fix (pattern A);
  - routes at the pinned commit where that same protection is missing (pattern B, within §1.5);
  - siblings we add to our own copy of the code.

### 1.4 Why the first drafts miss
- **Not portable.** They tell the agent to read files on this machine (`builder/*.md`, `research/*`),
  so they cannot run on DeepSeek or MiMo in Harbor or in a fresh chat without the repo.
- **The screener is a one-off.** It is a per-candidate reader for one top-30 pass. It has no slots
  for the weights or lessons version, no comparison across models, no known-outcome calibration set,
  and it puts scoring rules inside the prompt instead of in a script.
- **They use pattern B without its guardrails.** They ask for "real, unmodified gaps" with no scope
  limit, no disclosure register and no summary-level rule, and they do not separate it from
  pattern A.
- **They ignore the strongest outside evidence.** The peer pipeline's accepted hono task
  (`Sheraz/C_RESULTS.md`) was built only from
  the published fix's own sites: a second renderer, an array input shape and a must-keep-working
  clause.

### 1.5 Guardrails for pattern B (uncovered routes)
1. **Scope.**
   - Only the protection the published advisory is about, in that advisory's repository, at the
     pinned vulnerable commit.
   - Only routes into the same protected sink that the published fix left untouched.
   - No searching for other weakness types, other projects or other frameworks.
2. **Evidence.** A route counts only when a behavioural test on our pinned copy shows it. The
   builder confirms it; the screener's claim is a lead.
3. **Disclosure register.**
   - **Where:** `build/audit/uncovered-routes.tsv`, one row per route.
   - **Fields:** task, repo, advisory, a one-line description of the mechanism, and whether the
     route is still present in the latest release (`yes`, `no` or `unknown`, from a read-only look
     at current upstream code).
   - **Disclosure status:** `pending client decision` until NEXT-STEPS item 4 is settled.
   - **Hold:** a task with a route still present upstream is not shared outside the project until
     the client has decided on disclosure.
4. **Write-ups at summary level.** Notes, manifests and reports describe a route in one line: the
   protection, the route and the file:line. Never step-by-step exploitation. The tests are the
   detail.

---

## 2. Sources

Everything is inside `cwe-bench/`, except the handoff conversation itself. The prompts **embed a
digest** of these sources, so they run without the repo. They do not tell the agent to read them.
The sources are what the person writing the templates reads, and what each digest is regenerated
from when a source changes.

### 2.1 Shared by both files
| Source | What it gives the templates |
|---|---|
| `plan.md` §1, §3 | The goal (100–200 tasks; both models pass@3 = 0; the failure is the model's), the acceptance rule, and what round 1 taught |
| `builder/NEXT-STEPS.md` | Process order, working rules (timeouts and API cuts are never failures; no tests after a solve without approval), and next step 3, which defines these two files |
| Handoff conversation, 2026-10-16 (messages 297, 308, 312, 350–355) | The request itself, the safe framing (published, already-fixed advisories; building the benchmark), what was stopped, "screen hosts not advisories", and the "compare models, never reroute" rule |
| `RESULTS.md` "Round 2" and `build/audit/ledger.md` (regenerated with `build/audit_results.py`, the only source of truth for verdicts) | Known outcomes per host and model: the labels for calibrating and comparing models |
| `build/audit/trials.tsv`; per task `build/<task>/notes.md`, `FAIRNESS.md` and each run's `postmortem-*/verdict.json` | Per-attempt scores, and *why* each run failed or solved, so the digest's lessons cite audited evidence |
| `research/round1-analysis/B-failure-modes.md` §2.2–2.3, §3a, §4 | Why models fail (they judge wrongly about sites the report does not name), what they always catch, the 8 shapes |
| `builder/BRIEF-trap-stack.md` | Pattern B's evidence (the any-setter base that beat DeepSeek 6/6; sib2's real gaps), and the round-2 lessons: distance (marshmallow), a reason to dismiss (jackson-databind-readonly), a producer that is infrastructure and not a handler (better-auth), and Hadi's shape with its controls |
| `research/trap_tally.tsv` | Measured miss counts per shape and model |
| `Sheraz/C_RESULTS.md` and `Sheraz/cwe-bench_findings_2026-10-16.zip`, plus `research/peer-analysis-2026-10-16.md` (saved 2026-10-16) | Pattern A's evidence, on published advisories: hono accepted; nltk, the MCP SDK and undici broke a model; patterns P1–P10; DoS 0 of 7; break rate by family |

### 2.2 Screener prompt only
| Source | What it gives |
|---|---|
| `sourcer/index/candidates.sqlite` and `sourcer/README.md` (column list, `c_*` computed and `j_*` judgement columns, `score_read`) | The candidate pool (1,462 published, fixed advisories) and the judgement fields the screener's output must fill |
| `sourcer/rerank-v4-draft/` (`README.md`, `rerank.py`, `host-rank-all.tsv`, `host-shortlist-40.tsv`) | The computed pre-rank that picks which candidates are screened, and its known limits (repo size known for only a third; trap proxies fire broadly) |
| `sourcer/weights.json` (v3) and `rerank.py` (v4-draft) | The weights. A slot: the scoring script applies them, not the prompt |
| `research/round1-analysis/A-screener-validity.md` | Which signals failed to predict difficulty (so the prompt does not ask for them) and proposed new features |
| `research/round1-analysis/B-failure-modes.md` §3c | Code signals a reader can check near the fix, one per shape |
| `research/round1-analysis/D-computed-s2.md` | S2a and S2b (check plus producer in another file): what is computable and what needs a reader |
| `ALGORITHM.md` "Trap calibration" and "Learning loop" | How screener output feeds calibration and the refit of the weights |

### 2.3 Task-build prompt only
| Source | What it gives |
|---|---|
| `builder/BUILDER.md` §3a–3j, "Manifest", "instruction.md", "Run the gate", "Report back", gotchas | The authority for every build rule. The template's core is a digest of it |
| `builder/BUILDER-stacking.md` | The variant for a task that stacks several published advisories |
| `builder/templates/`, `harness/claude-code.Dockerfile.snippet`, `harness/smoke-task/` | The files and layout the builder fills |
| `builder/gate.py` (`WRONG_FIX_CLASSES`, static checks) | What the gate enforces, so the template never contradicts it |
| `builder/BLIND-FIX-BRIEF.md`, `builder/FAIRNESS-REVIEW-BRIEF.md` | The next stages' needs: what the builder must leave for them |
| `research/round1-analysis/B-failure-modes.md` §3b, §4 | Test shapes that caught each defect; instruction-wording rules |
| `research/own-runs/FINDINGS.md`, `research/round1-analysis/C-pipeline-lessons.md` | Test faults and pipeline faults to prevent (the §3g origin; about half of round-1 time lost) |
| `research/instruction-experiment.md` | Wording is hygiene, not the difficulty lever |
| Worked examples: `tasks/` and `build/` for `jackson-databind-sib2` (passed, both models 0/3), `better-auth-sso-endpoints` (3 fairness rounds, then solved), `marshmallow-readonly-sib`, `jackson-databind-readonly`; the hono dossier (peer, accepted) | One pass and three instructive misses, as examples of manifest, traps, notes and FAIRNESS.md |
| The asyncssh session prompt (2026-10-15, "Written for: a fresh Claude Code session ... Paste this:") | A pasteable build prompt that ran without being stopped: a format reference |

### 2.4 Used with care, or not at all
- **The trap brief's "real, unmodified gaps" line.** Use it for pattern B only, together with the
  §1.5 guardrails. It is not an open licence to hunt.
- **`sourcer/shortlist-20.*` and v2 weights.** History only. Their method did not predict
  difficulty.
- **`sourcer/host_screener.py`.** Untracked, written by a stopped agent with a cut-off brief; not
  reviewed. Do not use it.
- **`research/partial-progress-60min.md`.** For the client conversation, not for either template:
  timeouts never count as failures.
- **Round-1 instructions.** They are examples of what not to write (409–687 words, names, counts).
- **`cwe-bench-sheraz-wt/skills/`.** Outside `cwe-bench/`, so not read for this spec. It may hold
  the peer pipeline's own prompts (`task_design_techniques.md`, `lessons_learned.md`); the user
  decides whether to use it.

---

## 3. Contents

### 3.0 Conventions for both files
- **Two parts per file:**
  - an **operator part**, never sent: version, slots, how to launch, comparison log, change log;
  - the **prompt**, sent verbatim between two marker lines.
- **Self-contained prompt.** Lessons and rules are embedded as a short, versioned **digest**. The
  prompt never says "read file X in the repo", so it runs as:
  - a Claude Code sub-agent;
  - a Harbor job (prompt = `instruction.md`) on DeepSeek or MiMo;
  - a paste into a fresh chat.
- **Slots** look like `{{NAME}}`. Weights, lessons and candidates are always slots, never edits.
- **Versions.** Each file has a version id (e.g. `screener-v1`, `build-v1`), and each digest has its
  own (`lessons-v1`). Every output records the versions that produced it, so outcomes trace back.
- **The same framing paragraph opens both prompts.** It says:
  - this is benchmark construction from one published, already-fixed advisory;
  - the work is local;
  - mechanisms are described in one line, with no exploit write-ups;
  - the agent stays inside the advisory's own protection, in its own repo and pinned commit (§1.5).
    Anything outside that scope that it happens to notice gets one line in its report and is not
    built on.
- **Stops are handled by narrowing.** If a run is stopped, the operator narrows the prompt. It is
  never re-run on another model to get past the stop.

### 3.1 Screener prompt file (`builder/SCREENER-PROMPT-v1.md`, kept in `builder/` with the other briefs)

**Operator part**
1. Version and date; the digest version it embeds; the weights version that scores its output.
2. Slots:
   - `{{LESSONS_DIGEST}}`;
   - `{{CANDIDATE}}`: advisory ids, repo, CWE, summary, vulnerable commit, fix commit(s), computed
     `c_*` signals;
   - `{{CODE_LOCATION}}`: where the code at the vulnerable commit and the fix diff are. In Harbor
     they are pre-fetched into the image, so the run is offline.
3. Launch modes. For Harbor: a task folder whose `instruction.md` is the prompt, an environment with
   the pre-fetched code, and the output at `/output/host.json`, checked by a script.
4. **Calibration set**: hosts with known, audited outcomes.
   - **Both models failed:** jackson-databind-sib2 (pattern B); hono (peer; pattern A).
   - **DeepSeek only:** jackson-databind-sib (B); the MCP SDK (Hadi; peer; A); nltk (peer; A).
   - **Solved:** a spread of round-1 and round-2 tasks (marshmallow, jackson-databind-readonly,
     better-auth) and peer solves (pyload, GitPython).
5. **Model comparison protocol.**
   - **Models:** Fable 5.1, Opus 4.8, Opus 5.5, DeepSeek V4.1 Flash, MiMo-V2.6-Pro, and any other
     available.
   - **Runs:** the same prompt, on the same calibration hosts, once per model.
   - **Metrics:**
     - field agreement with a reference reading (Opus 5.5, checked by the lead);
     - share of file:line claims that are wrong (checked by script);
     - whether the known breakers rank above the solved hosts;
     - cost and time;
     - stops.
   - **Choice:** the cheapest model that meets the bar does routine screening.
6. Comparison log (a table) and change log.

**Prompt, in order**
1. **Framing paragraph** (shared, 3.0).
2. **Goal.** In about 5 lines:
   - what a task is: the solver gets the vulnerable code and a report; hidden behavioural tests
     score its fix;
   - the acceptance rule: both target models fail 3 finished attempts by their own judgement, and
     the task is fair: findable from the report and the code, and fixable in about 45 minutes.
3. **`{{LESSONS_DIGEST}}`.** lessons-v1, under about 400 words, built from §2:
   - **Where both models fail.** They find the code and diagnose the root cause. They fail on scope:
     - they treat the report's examples as the full list;
     - they fix only the input shape they reproduced;
     - they verify through their own fix's path, then stop;
     - they read a must-keep-working clause as permission to leave a sink open;
     - they miss state that crosses save/reload or serialization;
     - they miss a second public API or a lower-level constructor;
     - they argue an observed leak out of scope.
   - **Model profiles.** DeepSeek talks itself out of fixing what it found. MiMo explores narrowly
     and over-hardens.
   - **What never worked:**
     - encoding, verb, protocol or role variants;
     - more routes of one concept;
     - single-location fixes;
     - resource exhaustion (0 of 7);
     - small libraries;
     - a protection documented with no exceptions;
     - instruction wording alone.
4. **Inputs**: `{{CANDIDATE}}`, `{{CODE_LOCATION}}`.
5. **Steps.**
   1. Read the advisory and the fix diff.
   2. Map every changed site to the public entry point that reaches it.
   3. Fill each observation from the code at the vulnerable commit.
   4. Check buildability.
   5. Record what you could not verify.
6. **Observations.** A fixed list; each value comes with file:line evidence, or `unknown`:
   - **O1, entry points:** the number of distinct public entry points that reach the flaw the
     published fix closes.
   - **O2, out-of-scope-looking site:** one of `second_implementation`, `lower_level_api`,
     `wrapper_or_composition`, `save_reload_or_serialization`, `defaults_or_merge_route`,
     `legacy_path`, `none`.
   - **O3, reason to dismiss:** the one-line argument a solver could make for leaving that site
     alone.
   - **O4, distance:** files and packages between the report's natural landing point and the
     farthest site; repo size.
   - **O5, coupled behaviour:** a legitimate behaviour next to the sink that an over-broad fix
     breaks.
   - **O6, input shapes:** the input-shape variants the published fix handles.
   - **O7, producer:** the kind (`schema`, `serializer`, `cache`, `mapper`, `config_loader`,
     `handler`, `none`), and whether the check calls it.
   - **O8, uncovered routes (pattern B):** routes into the same protected sink where the
     advisory's protection is also missing and the published fix made no change. Each one needs
     file:line, a reason to dismiss, its distance from the landing point, and whether it is still
     present in the latest release (`unknown` is allowed). Within the §1.5 scope only.
   - **O8b, injection room:** a plausible place in our copy to add a sibling of the same mechanism,
     and why a maintainer could have written it.
   - **Pattern fit:** which patterns the host supports (`A`, `B`, `A+B`, `injection_only`, `none`),
     derived from O1–O8b.
   - **O9, weakness family:** plus a DoS flag.
   - **O10, build:** toolchain, services, offline after build, the project's tests for the area.
   - **O11, fix effort:** in minutes.
   - **O12, red flags:** from a fixed list (the advisory's regression tests are already in the
     vulnerable commit; needs a GPU, kernel or GUI; too many fix commits; tiny or giant repo).
   - **O13, recall risk:** how widely the advisory is written up.
   - **Judgement columns:** the `j_*` columns of `sourcer/README.md`, derived from the above.
7. **Output.** A fixed JSON schema (field names, enums, `evidence` per field, `unverified` list,
   versions). **No score field**: the script scores.
8. **Limits.**
   - A time box per candidate.
   - No Docker.
   - No running of exploit code.
   - No network beyond the code location given.
   - No other repositories.

**Outside the prompt, same folder**
- **The scoring script:** observations × `weights.json` (versioned) → `score_read` → shortlist.
  This extends `rerank.py`.
- **The schema validator:** checks every file:line and enum.
- **Outputs:** in `sourcer/review/<screener version>/<entry_id>.json`, merged into the index's
  `j_*` columns by script.
- **Learning loop:** after each trial batch, add the outcomes to `research/trap_tally.tsv`, refit
  the weights, regenerate the digest, bump the versions, and re-screen.

### 3.2 Task-build prompt file (`builder/TASK-BUILD-PROMPT-v1.md`)

**Operator part**
1. Version and date; the digest versions it embeds; the BUILDER.md revision the digest was made from.
2. Per-task slots (3.2, "Per-task section"), and how to fill them from the screener record.
3. Launch modes: Claude Code sub-agent, or a paste into a fresh session; a Harbor job later.
4. What follows the build, each with its own brief:
   - blind fix;
   - fairness review;
   - strict gate;
   - trials;
   - per-run audits.
5. **Model comparison protocol** for builders:
   - static and full gate pass on the first try;
   - fairness verdict in the first round;
   - number of repair rounds;
   - wall time;
   - stops.
   (A target model may build, but never writes the blind fix for its own task.)
6. Comparison log and change log.

**Shared core of the prompt, in order**
1. **Framing paragraph** (shared, 3.0). Tests check that the published flaw is closed, using
   harmless inputs and markers.
2. **Goal and acceptance**, the same as the screener's, plus:
   - timeouts and API cuts never count;
   - a fix must take a careful engineer about 45 minutes or less.
3. **Design digest.** Where difficulty comes from, in order of evidence:
   - the published fix's sites beyond the report's example, one of them in a module that looks out
     of scope, with a reason to dismiss it and distance from the landing point;
   - input-shape variants;
   - a coupled must-keep-working behaviour, tested functionally;
   - a producer that is infrastructure the check does not call;
   - for pattern B, uncovered routes with a reason to dismiss: the strongest single-model lever so
     far (DeepSeek 6/6). Each one needs a test on our pinned copy, a row in the disclosure register,
     and a one-line write-up (§1.5).

   For injected siblings: siblings we add to our copy must be:
   - realistic and reachable through the real entry point;
   - covered by a stated invariant;
   - findable by the blind fix.

   What never works: the list in 3.1, item 3.
4. **Environment rules** (BUILDER 3a, 3h):
   - the vulnerable commit, with `/app/.git` removed;
   - every dependency installed, offline after the build;
   - no test code in the image (stubs only);
   - the agent layer appended;
   - the project's own tests for the area pass.
5. **Instruction rules** (BUILDER 3i, B §4):
   - **Content:** the system, one impact with one user-level trigger, and the invariants;
   - **Contracts:** the refusal form, any interface the tests need, preservation clauses, and a
     legitimate magnitude next to any attack magnitude;
   - **Never in the instruction:** names, root cause, fix, a count or a variant list;
   - **Examples** are marked as examples;
   - **The constraints block** closes it;
   - **`leak_terms`** go in the manifest.
6. **Test rules** (BUILDER 3c, 3g, B §3b):
   - behavioural, through the real entry point;
   - one security test per variant and form;
   - a coupled functional test per trap;
   - refusal means any client error plus no side effect;
   - expected values are computed in the test, never by calling product code;
   - stubs answer per resource and verb;
   - every contract is stated in the instruction;
   - no network;
   - JUnit output with the template `test.sh` and `score.py`.
7. **Proof:**
   - the oracle (source-only upstream fix);
   - one `security_fail` patch per trap;
   - the wrong-fix catalogue (`WRONG_FIX_CLASSES`, a patch or `n/a: why` for each);
   - a `functional_fail` patch;
   - `pass` patches of kind `hardening` and, where plausible, an alternative fix;
   - `"strict_gate": true`.
8. **Deliverables:** the file tree and the manifest fields (`traps`, `wrong_fix_catalogue`,
   `patch_checks`, `leak_terms`, `builder_prompt_version`, `pattern`), plus `notes.md` with start
   and end UTC. For pattern B, one row per route in `build/audit/uncovered-routes.tsv`.
9. **Gate stages to run, in order, one at a time:** static, nop, oracle, patches. Not to do:
   - the blind patch;
   - `FAIRNESS.md`;
   - trials;
   - any target-model run.
10. **Machine limits:**
    - the shared 8-CPU / 12 GB VM;
    - never prune images or the build cache;
    - never stop containers it did not start;
    - one Docker job at a time;
    - scratch in `~/.tb-graders/cwe/work/<slug>/`;
    - edit only `tasks/<slug>/` and `build/<slug>/`;
    - no commits.
11. **Abandon rules:**
    - the flaw does not reproduce through a real entry point;
    - it needs network at run time;
    - it needs a GPU, kernel or GUI;
    - the tests are flaky;
    - no design meets the bar.

    The builder reports why, and never ships a weaker task.
12. **Report format**, under 400 words:
    - each gate stage's result;
    - each lever or trap in one line;
    - the instruction's word count;
    - unverified guesses;
    - fairness concerns;
    - for pattern B, each route's register row;
    - anything noticed outside the §1.5 scope (one line, nothing built on it).

**Per-task section of the prompt (the only part that changes per task)**
- `{{SLUG}}`, `{{PATTERN}}` (`A`, `B` or `A+B`), `{{TRACK}}` (`mined`, `stacking` or `injected`).
- `{{ADVISORY}}`: ids, repo, CWE, summary; `{{VULN_COMMIT}}`; `{{FIX_COMMITS}}`.
- `{{FIX_SITES}}`: the published fix's sites with their entry points, from the screener (O1–O7).
- `{{UNCOVERED_ROUTES}}`: for pattern B, the screener's O8 leads, which the builder must confirm.
- `{{DESIGN_PLAN}}`, chosen by the lead:
  - the main lever;
  - the sites and variants to test;
  - the coupled behaviours;
  - for the injection track, each sibling to add, where it goes, and why it is realistic.
- `{{HOST_NOTES}}`: build gotchas, things to avoid, credit lines (for example Hadi's shape).

### 3.3 Done when
- Both files exist with the parts above.
- The screener has run on the calibration set with at least three models. A model is chosen and
  logged.
- The builder template has produced one pattern-A task and one pattern-B task, each passing the full strict gate (blind fix and
  fairness review included) with no hand edits to the shared core.
- Neither template was stopped in those runs. Any stop is logged with the narrowing it led to.
