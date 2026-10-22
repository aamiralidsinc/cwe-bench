# Better patterns: findings and pending changes (2026-10-19)

**Purpose.** This file holds what we learned on 2026-10-19 from the sibling-injection analysis
(`reports/SIBLING-INJECTION-PATTERNS.md`).
- **§2-§8 were applied to the live pipeline on 2026-10-19** (VM `~/cwe-bench`, mirrored to this
  repo where a local copy exists). See "Applied 2026-10-19" below §0. §1 is research, not applied.
- **Status of each item:** `PENDING` = not done; `PARTIAL` = partly present in the pipeline;
  `FIXED` = done.

**Mechanism codes used below.** These are the labels from the analysis report, not builder
vocabulary:

| Code | Pattern | One line |
|---|---|---|
| M1 | Parallel entry point | another handler, command, endpoint or option reaches the same protected sink without the guard |
| M2 | Second implementation | a separate copy of the guarded logic: another package, fallback backend, adapter, transport or legacy version |
| M4 | Feature absent | the route never had the protection at all |
| M5 | Merged or defaults route | the value arrives through defaults, merge, inheritance or stored config |
| M6 | Data producer off the check's path | a schema, loader or table builder feeds the check's data through a path the check never calls |
| M8 | Parser differential | prefix vs path segment, case, symlink, separator split, nested expression |
| M11 | Coupled contract | a linked legitimate value next to the hidden one must keep working |

---

## 0. Placement map: where each fix goes (★ = primary, ✓ = also applies)

Summary of §2–§8 across the pipeline stages. §1 is a research direction, not a placement.

| § | Fix | Screener | Builder | Faircheck | Fairfix | Hardening |
|---|---|:--:|:--:|:--:|:--:|:--:|
| **§2** | General rule: never **name** nor **describe** a sibling's surface — state the property once | — | ★ instruction wording (`TASK-BUILD-PROMPT`, `BUILDER §3i`, `BUILD-PROMPT`) | ✓ reject any task whose instruction lists/points at surfaces | ✓ never add surface-naming/listing wording | ✓ never add a surface list when planting traps |
| **§3** | Delete "word each property to cover every route / one natural list" | — | ★ remove (`TASK-BUILD-PROMPT:168-170`, `BUILDER §3i`) | — | — | — |
| **§4** | Resolve template contradiction (bans route lists yet asks for them) | — | ★ `TASK-BUILD-PROMPT:168-186` + contracts `:171-176` | — | — | — |
| **§5** | Where- vs how-patterns | ★ score hosts by **how-type** sibling count, not route count | ✓ pair a general instruction with ≥1 how-type sibling | — | — | ✓ add how-type depth, not route lists |
| **§6** | M6 producer off the check's path | ✓ `O7_producer` (already recorded) | ★ add the 5 missing checks to the template | — | — | ✓ may add an M6 sibling |
| **§7** | M1/M2 second implementation | ✓ find M2 candidates (search the low-level primitive across packages) | ★ add M2 as a lever; keep M1 only as an extra | — | — | ✓ may add an M2 sibling |
| **§8** | Unfixed/absent route = model failure, not out-of-scope | — | ✓ revise Pattern B (`TASK-BUILD-PROMPT:108-111`) | ★ accept the general rule as covering every route; apply the 2 conditions | ★ don't "fix" by removing/naming a route; only repair real defects | ★ `HARDENING-PROMPT:18,29` |

**§2 is the must-have.** It is the pattern that actually makes the models fail, and it touches four stages
(builder writes it, faircheck enforces it, fairfix must not undo it, hardening must not reintroduce a
list). A pipeline without §2 produces checklists that get solved — so building without §2 means nothing.

### Applied 2026-10-19

Each item was applied one at a time, one source at a time, and pushed to the VM after each item. The
VM originals are kept as `<file>.bak-20261019`. Nothing was blocked.

| § | Screener | Builder | Fairness check | Fairfix | Hardening |
|---|---|---|---|---|---|
| §2 | — | `TASK-BUILD-PROMPT-v1.md` "Never write" + final self-check; `BUILDER.md` §3i; `SELFDESIGN-PLAN.md` | `FAIRNESS-REVIEW-BRIEF.md` new step 3a, "Required: generalize" list (not a gate-a reason) | `run_fairfix.sh` hard rule | `HARDENING-PROMPT.md` hard rule (prefer no instruction change) |
| §3 | — | `TASK-BUILD-PROMPT-v1.md` invariant bullet; `BUILDER.md` §3i | — | — | — |
| §4 | — | `TASK-BUILD-PROMPT-v1.md` contracts bullet (stated once, never per route) and §3i contracts | — | — | — |
| §5 | `SCREENER-PROMPT-v2.md` new `lessons-v2` digest; `SELECT-PROMPT.md` scoring (how-type first, injection room an extra) | `TASK-BUILD-PROMPT-v1.md` "at least one how-type lever"; `SELFDESIGN-PLAN.md`; `BUILDER.md` §3j | — | — | `HARDENING-PROMPT.md` prefer how-type levers |
| §6 | already recorded (`O7_producer`) | `TASK-BUILD-PROMPT-v1.md` Design item 5, all producer rules | — | — | `HARDENING-PROMPT.md` producer lever |
| §7 | `lessons-v2` (how to find one); `SELECT-PROMPT.md` (under §5) | `TASK-BUILD-PROMPT-v1.md` Pattern A, second implementation | — | — | `HARDENING-PROMPT.md` second-implementation lever |
| §8 | `lessons-v2` (never-protected route) | `TASK-BUILD-PROMPT-v1.md` Pattern B | `FAIRNESS-REVIEW-BRIEF.md` steps 1 and 4, gate a (the two conditions) | `run_fairfix.sh` hard rule | `HARDENING-PROMPT.md` uncovered routes |

The fairness brief's machine-readable ending (`GATE_A`, `NEEDS_HUMAN_REVIEW`) is unchanged. The local
`FAIRNESS-REVIEW-BRIEF.md` was older than the VM's two-gate version; it now matches the VM.

### Still open before a new run

1. **Regenerate BUILD-PROMPTs** built from the old template. Each `build/<slug>/BUILD-PROMPT.md`
   embeds a copy of `TASK-BUILD-PROMPT-v1.md`, so the 41 `-mm` prompts (and any `-ds` prompt not yet
   built) still carry the old rules. Rerun `pipeline/prepare_lane.py` for each lane, after the
   selection is redone if you want the new SELECT-PROMPT scoring to apply.
2. **Use `lessons-v2`** in `{{LESSONS_DIGEST}}` for any new screener run. The digest is pasted by
   hand; nothing fills it automatically.
3. **Already-built tasks** were written under the old rules, and most describe their siblings'
   surfaces. Re-run the fairness check (new step 3a) and fairfix on any of them before trialling it
   again.
4. **VM-only files** (`SELECT-PROMPT.md`, `SELFDESIGN-PLAN.md`, `HARDENING-PROMPT.md`,
   `run_fairness.sh`) have no copy in this repo yet.

---

## 1. PENDING, high priority: explore stacking further

The one audited both-model breaker, jackson-databind-sib2, is a stacked task. We moved away from
stacking after round 1 without exploring it properly.

### 1.1 "Stacking" means two different things here

| | Branch C stacking (round 1) | Trap stacking (jackson-databind-sib2) |
|---|---|---|
| What is stacked | several **different real vulnerabilities** co-present in one checkout | **one** protection, with several real routes of **different mechanism kinds** |
| Tasks | actualbudget, argo-workflows, asyncssh, cloudreve, filament, ruby-saml, stigmem, trigger-dev | jackson-databind-sib2 |
| How the report described them | one section per flaw: each flaw named, and the count revealed (BUILDER.md §3i) | one example and one rule; routes 2-4 not named |
| Result | solved offline (29 of 30 pairs, together with the mined tasks) | both models 0/3, audited |

### 1.2 What made jackson-databind-sib2 fail both models

Source: `reports/jackson-databind-sib2-breaker.md`.
1. **One rule, four real routes, none named.** The report gives one example (route 1) and states the
   rule over the property: no input may set a restricted property "whatever the type looks like,
   however the object is built or populated, and whether the input creates a new object or is
   applied to an existing one".
2. **One route with the protection absent** (M4, the catch-all). All 6 attempts left it open. The
   models found it and dismissed it ("upstream doesn't support it").
3. **A coupled legitimate value next to each hidden route** (M11). 4 of 6 attempts broke one, which
   scores 0.
4. **A how-type route** (the record-id stand-in carries no view information). The correct fix keeps
   registering the identity and skips only the property write. 5 of 6 attempts left a write open or
   broke the links.
5. **A large codebase, and distance** from the landing site.
6. **Built in steps.** The first version (route 1 plus the catch-all) beat DeepSeek 6/6, but MiMo
   solved it. Adding the record-id and update routes, each with its own coupled value, made MiMo
   fail as well.

### 1.3 Why the other stacked and trap-stacked tasks were solved

| Task | Why it was solved |
|---|---|
| Branch C tasks (8) | each vulnerability was a separate, named concept with its own section; each fix was derivable from the advisory |
| marshmallow-readonly-sib | small library, no distance: DeepSeek found every trap within 2 minutes |
| jackson-databind-readonly | same codebase, but READ_ONLY is documented with no exceptions, so nothing invited an out-of-scope reading |
| better-auth-sso-endpoints | the "producer" was a request handler, which the model read whole |
| round-2 template and pilot tasks | mostly M1/M2 routes of one concept, and instructions that describe each sibling's surface (§2) |

### 1.3a Analysis (2026-10-20): why stacking worked once and not elsewhere

Data: the 62 tasks with trial data. For each failed run, the traps whose security tests failed
(VM verifier results). Raw and unaudited, apart from sib2.

**1. Redundancy: sib2 failed at least two independent parts in every run; the near-misses fail on one.**

| Task | What failed runs missed | Result |
|---|---|---|
| jackson-databind-sib2 | all 6 runs: the catch-all, plus a record-id write and/or a broken coupled value | breaker: removing any one route's tests still leaves all 6 below 1.0 |
| prompty-path-read-inj | T2 only, in every failed run | MiMo 0/3, DeepSeek solved |
| electron-builder-credential-leakage | one trap per run (T2 or T3) | MiMo 0/3, DeepSeek solved |
| siyuan-ds | T6 alone in its last run (0.94) | DeepSeek 0/3 |
| hermes-agent-ds | T7 alone in 2 runs | MiMo 0/3, DeepSeek solved once |
| airflow-info-exposure-inj | DeepSeek one trap per run, then solved | MiMo 0/3 |
| electron-builder-ds | T4 alone in 4 of 9 DeepSeek runs | MiMo solved once |

A task that rests on one hard trap is solved by the first run that gets that trap right. The
pipeline tasks have 4-16 traps, but they are routes of one concept that are fixed together, so in
effect they hold one trap.

**2. Complementary traps: each model needs a trap it misses, and the two models miss different
things.**
- **DeepSeek** misses a route where the protection is absent and there is a reason to dismiss it:
  - jackson-databind-sib catch-all, 6/6;
  - siyuan T6, 3/3;
  - electron-builder-ds T4, 9/9.
- **MiMo** misses coupled values (over-hardening) and how-type mechanisms:
  - sib2 C1 broken;
  - airflow, where every MiMo zero includes an over-broad functional failure;
  - the record-id stand-in in sib2.
- **Natural experiment:** sib had only the DeepSeek-type trap (DeepSeek 0/6, MiMo solved). sib2
  added MiMo-type traps (record id with coupled links, merge route, more coupled values), and MiMo
  failed 0/3. In sib2, MiMo also left the catch-all open in all 3 runs, which it had fixed in sib.
  One hypothesis: more independent traps leave less attention per trap. Not proven.

**3. Coupled traps are almost absent from the pipeline tasks.** Only the jackson family, russh-sib
and nhost carry two or more. Coupled traps are the main MiMo lever, and a functional failure scores
0.

**4. The other ingredients, each missing in a solved control:**

| Ingredient | Solved control that lacked it |
|---|---|
| a general instruction | sib7: the paraphrase listed the forms, and DeepSeek solved |
| a reason to dismiss | jackson-databind-readonly: same codebase, protection documented with no exceptions |
| distance | marshmallow-readonly-sib: small library |
| producer as infrastructure | better-auth-sso-endpoints: the producer was a handler |

**5. Branch C** stacked several separate bugs, but each was named in its own section and each fix
was derivable from its advisory: independent, but each one easy.

**What this means for building:** stack 3 or more traps that are each hard on their own, with
different dismissal reasons. Include at least one trap that DeepSeek misses (protection absent,
plus a reason to dismiss) and at least one that MiMo misses (a coupled value; a how-type
mechanism). Then a correct run must get all of them right. Check after the gate: a wrong-fix patch
that misses any single trap must score below 1.0, and no single trap should carry the task.

Caveat: one breaker, 1-6 runs per pair. This is a case study with natural experiments, not a
measured rate.

### 1.4 What to explore

1. **Replicate the sib2 recipe on other large libraries:**
   - one rule;
   - several real routes of different mechanism kinds;
   - at least one route where the protection is absent;
   - a coupled legitimate value on each hidden route;
   - none of the routes named.
2. **Ablate sib2 to find which ingredient carries the result.** Rebuild it with one ingredient
   removed at a time: no coupled values; no absent-protection route; no how-type route; routes
   named.
3. **Revisit Branch C with the §2 instruction rule.** Round-1 stacked tasks described every flaw;
   the `-inv` rewrites still gave each flaw its own property bullet. Branch C has never been tried
   with one general rule and unnamed co-present vulnerabilities.

---

## 2. Instruction rule: neither NAME nor DESCRIBE the siblings' surfaces (FIXED 2026-10-19)

The rule has **two parts. Keep both.**
1. **Never name a sibling:** no file, package, function, class, field or parameter name. This is
   already enforced by `manifest.leak_terms` and the static leak check.
2. **Never describe a sibling's surface in product terms either:** no clause that points at one
   route, operation, channel, object kind, stage or format.

**Why both parts.** If only part 1 is kept, builders describe the surfaces instead of naming them;
that is what the DeepSeek-built tasks did. If only part 2 is kept, a rewrite can drift back to
naming. State the security property once, in general terms, so that it covers every surface without
pointing at any of them.

**Evidence:**
- **DeepSeek-built and MiMo-built pilot tasks** (typo3, fission, gogs, n8n, mockoon, yamcs, theia,
  rsdoctor, orval, pimcore, olivetin):
  - the instructions name no code, but list each sibling's surface, often one clause per trap;
  - the scaled DeepSeek pipeline solved 30 of 30 tasks;
  - of the 98 planted siblings with trial data, 5 were missed.
- **Hadi's MCP task:** naming the reload path flipped DeepSeek from 0/3 to 3/3.
- **jackson-sib7:** a paraphrase that listed the any-setter forms took DeepSeek from 0/6 to finding
  them in 10 of 11 runs (`research/round1-analysis/B-failure-modes.md` §4).

**Word choice: a word that is general but is also the name of one surface is not allowed.** Use
wording that cannot be read as one stage or one entry point. Using such a word as a trick is unfair.

### Example: prompty T2 (prompty-path-read-inj, prompty-ds)

**Item 1: surfaces are named.** The rule lists four of them: "injected file contents, an included
text fragment, an inherited base document, and a referenced child prompt". The listing itself
already breaks the rule.

**Item 2: "loading" is both a general word and the name of one stage.**
- The rule says "No path … may cause *loading that document* to read a file outside the directory".
- The system section says documents come in through "the library's *public load call*".
- T2's child-prompt path is not read at load time. It is read later, when the prompt *runs* (wire
  projection and dispatch).
- A model can therefore read "loading" as "the load call", fix that stage, and stay inside the
  literal rule.

**Better:** state the outcome, not a stage. For example: "a path written in a prompt document must
never cause a file outside its directory to be read".

---

## 3. DEPRECATED instruction: "word each property so it covers every tested route … give one natural list"

**Do not follow it any more.** Model-built tasks that followed it read like checklists, and a
checklist gets solved (§2).

**Where it lived (REPLACED 2026-10-19 in both places; see "Applied 2026-10-19"):**
- `builder/TASK-BUILD-PROMPT-v1.md:168-170`, local and VM: "Word each so it covers every tested
  route and shape ("no value of X may …"). If there are several, give one natural list, never a
  count";
- `builder/BUILDER.md` §3i: "Word each so it covers the tested variants" and "for several flaws:
  one coherent list of properties in natural order".

**Why it came up (2026-10-16):**
- **Round-1 stacked tasks** had one report section per flaw, which revealed each flaw and the count.
  "One natural list, never a count" was meant to replace those sections.
- **Fairness:** everything a test requires must be findable from the instruction plus the code. So
  each tested route had to be covered by a property.

**What went wrong.** Model builders read "covers every tested route" as "mention every tested
route" and wrote one clause per route. The warning was already on record: B-failure-modes §4,
rule 1 says "never list a sibling's forms, types or phases", with sib7 as the case.

**Replacement (to apply later):** a property is fair when, read literally, it covers the route. It
does not have to point at the route.

---

## 4. Contradiction in the build template (FIXED 2026-10-19)

The same template both bans route lists and asks for them:
- `builder/TASK-BUILD-PROMPT-v1.md:181-186` ("Never write"): "a list of routes, spellings or roles";
  "anything that names or paraphrases a far site, an uncovered route or an injected sibling";
- `:168-170`: "Word each so it covers every tested route and shape … give one natural list";
- `:171-176` (contracts, lines 173-174): "any interface or field name a test uses" and preservation clauses. When
  these are written per sibling, they describe the sibling's surface.

Builders resolve the conflict towards listing. The DeepSeek and MiMo pipelines use this template:
`pipeline/prepare_lane.py` → `build_prepare.py` → `BUILD-PROMPT.md`. The 41 `-mm` BUILD-PROMPTs
already generated carry the OLD text and must be regenerated before they are built (see "Still open").

---

## 5. Rule for screening and building: where-patterns vs how-patterns (FIXED 2026-10-19)

1. **Where-patterns (M1, M2, planted routes) only count if the instruction stays general.**
   - Their only difficulty is finding where the sibling lives. With a surface list, they are wasted
     build cost.
   - **Evidence:** planted M1/M2 siblings were missed 5 times out of 98 under surface-describing
     instructions.
   - **Counter-evidence:** where the surface was not described, real ones bit:
     - electron-builder-ds T2: the differential downloader's own redirect code; the instruction
       says only "every request … at every redirect";
     - airflow T3: the instruction says only "however the team-scoped value is supplied".
2. **How-patterns (a producer two layers down, a parser differential, a coupled contract) can carry
   difficulty even with a fairly specific instruction.** Here the hard part is the mechanism, not
   the location:

   | Task | Pattern | What was stated | Result |
   |---|---|---|---|
   | protobuf.js-ds T3 and T7 | M6 | "an enum identifier … an emitted table" | missed by both models: knowing enum names are affected does not show that the bug sits in the table builder below the parser |
   | airflow T10 | M8 | "nothing may be assumed about the characters a name contains" | missed by both: the first-separator split |
   | jackson-databind-sib2 C1 | M11 | the must-keep-working value | broken in 4 of 6 runs |

   - **Limit:** a producer behind a path that is easy to follow still falls once it is named
     (Hadi's MCP task). The how-pattern needs real depth.

**Use in screening:** score hosts by how many how-type siblings their real code offers. Do not
score them by route count.

**Use in building:**
- pair a general instruction (§2) with at least one how-type sibling;
- treat where-type siblings as extra, worth something only under a general instruction.

The strongest tasks combine both. jackson-databind-sib2 is the example.

Caveat: these are small numbers (1-3 runs per model) and raw trial results; protobuf.js-ds is a
suspected test-artifact task. Treat this as a direction to test.

---

## 6. M6, data producer off the check's path (FIXED 2026-10-19; was PARTIAL)

**What it is.** The fix needs two changes:
1. the **check** the report leads to;
2. the **data producer** the check depends on (a schema, serializer, loader, config resolver or
   table builder), which sits in another file and which the check never calls. The data reaches the
   check through a separate path, for example saved and reloaded.

**Examples:**

| Task | Check | Producer | Result |
|---|---|---|---|
| Hadi's MCP SDK | the issuer check | zod schemas strip the issuer on reload | DeepSeek 8/8 missed |
| airflow T3 | sensitivity masking | the config loader's spelling of team environment variables | missed by both |
| protobuf.js-ds T3 | the parsers' enum lookup | the enum values table | missed by both |

**Why models miss it:**
- They trace downwards, into what the check calls, and never upwards, to where its inputs come from.
- The repo's own tests rarely cover save-and-reload or config-loading paths, so passing them proves
  nothing.
- A fallback such as "if the field is missing, allow" looks like compatibility code, so it is kept.

**Already in the pipeline:**
- `TASK-BUILD-PROMPT-v1.md`, Design item 5: one line, plus "counts only if the producer is
  infrastructure, not a request handler";
- `BUILDER.md` §3j: listed as a shape that beat DeepSeek;
- the screener records an `O7_producer` field;
- the full rules are in `builder/BRIEF-trap-stack.md` and `ALGORITHM.md`, but the DeepSeek and MiMo
  lanes do not read those files.

**Missing from the build template (to add later):**
1. Verify that the check does **not** call the producer. If it does, the model follows the call and
   fixes it (Hadi's Semaphore control).
2. The report describes impact only through the check's path and states the property abstractly
   ("including data saved earlier"). It never points at the producer or the reload path.
3. Avoid fixes where the check cannot compile without the producer change: that forces the model to
   find it.
4. Hidden tests must not need a field or function name the model would have to guess.
5. Prefer producers deep in internal machinery (a table builder, a schema layer). A producer behind
   a path that is easy to follow falls once anything points at it (§5).

---

## 7. M1 and M2, with M2 in a narrower form (FIXED 2026-10-19; was PARTIAL)

**What M2 (second implementation of the guard) is.** The same guarded operation exists twice or
more in the codebase, each copy with its own code: a fallback backend, another package, another
transport, a legacy version.
- The report's example goes through copy 1, and the protection must be added to every copy.
- **How it differs from M1:** M1 is another door into the *same* code. M2 is *separate* code doing
  the same job, so fixing copy 1 changes nothing in copy 2.

**M2 examples:**

| Task | Protection | Copy 1 (covered) | Copy 2 (missed) | Result |
|---|---|---|---|---|
| electron-builder-ds T2 | no credential on a cross-origin redirect | the main HTTP helper | the differential (blockmap) update downloader, which issues its own requests; real upstream code, still on main | missed by both |
| hermes-agent-ds T7 | third-party tool results are wrapped as untrusted data | the main agent loop | the Codex transport's own projector, which builds tool messages itself | missed by both |
| litellm-ds T2 | destination check on model selection | the shared request processor | the image endpoint's own model-selection block | MiMo once |

**Why models miss it.** The model fixes the copy the example hits, re-runs the example, sees it
pass, and stops. The other copy sits in another package or transport and looks like a different
feature, so the model never asks "what else performs this operation?"

**Already in the template:**
- **M2** appears as a kind of Pattern A far site: "a second implementation, a lower-level public
  API, a wrapper".
- **M1** is not described as a lever. The template says "Never add … more routes of one concept",
  yet the model builders planted mostly M1/M2 siblings.

**What the data says:**
- **Planted M1/M2 siblings almost never bite:** 5 of 98.
- **Real M2 bites when it sits at distance and its surface is not described:**
  - electron-builder-ds T2, the differential downloader: missed by both;
  - hermes-agent-ds T7, the Codex transport projector: missed by both;
  - litellm-ds T2, the image endpoint's own model selection: MiMo once.
- **M1 is the weakest:** 12 of 99, under the current instructions. The same M1 under a general
  instruction has not been measured.

**To add later:** M2 as "a real second implementation of the same operation, in another package or
transport, not described in the instruction".
- Find candidates by searching for the low-level primitive across packages (redirect following,
  header copying, file writes, message construction), fallbacks, transports and legacy versions.
- Keep M1 only as an extra under a general instruction (§5).

---

## 8. Leaving an unfixed upstream route open under a general rule is a model failure (FIXED 2026-10-19)

**The principle.**
- The instruction asks for the security property to hold everywhere. The pinned code still has
  routes where it does not hold, which upstream never fixed.
- A correct fix closes those routes too: the instruction requires the protection to exist, not to
  copy what upstream happened to fix.
- A model that fixes only the reported site, or only what upstream fixed, has **failed**. That is a
  documented failure pattern ("fixes the reported scope, not the stated property"). Record it in
  `research/trap_tally.tsv` like any other miss.
- **The same holds for a route where the protection never existed** (M4). The rule requires the
  protection, so its absence is the flaw.

**Fairness reviewers must not flag these routes** as "beyond the advisory", "out of scope" or "not
what upstream fixed". The reason a model gives for skipping one ("upstream doesn't support it", "not
a security boundary") is the model's own judgement, not a fairness defect.

**A miss counts only when both conditions hold:**
1. **The general rule, read literally, covers the route.** If its wording leaves the route out, the
   miss is our wording's fault. Example: prompty T2, where "loading" excludes a read that happens
   at run time (§2).
2. **The test fails only when the protection is really missing.** If it also fails a correct fix,
   the miss is our test's fault:
   - vitest-api-fs-authz-inj: the tests bypass the dispatcher where a correct guard can sit;
   - backstage-ds: the attack was blocked, but the test demanded one error class and its mock
     context crashed first.

When either condition fails, repair the task; do not count the run.

**Where it must go (to apply later):**

| Stage | File | Current text to revise |
|---|---|---|
| Builder | `builder/TASK-BUILD-PROMPT-v1.md:108-111` (local and VM) | Pattern B says unfixed routes are ones "a solver can argue … were never covered". State instead that the task's property covers them, and that leaving one open is a failure. |
| Hardening | VM `builder/HARDENING-PROMPT.md:18` ("Uncovered routes (O8)") and the hard rules at `:29` | Add that a new unfixed route qualifies when the existing general rule already covers it, and that a solver leaving it open is a failure, not a fairness gap. |
| Fairness check | `builder/FAIRNESS-REVIEW-BRIEF.md` items 1, 4 and 5 (local and VM) | Accept the general rule as the covering sentence for every route it covers literally. Do not mark a real unfixed upstream route unfair for being outside the published fix. Do check the two conditions above. |
| Fairness fix | `run_fairfix.sh`, the inline prompt at `:17` ("Apply EVERY 'Required' change") and `:25` ("Hard rules") | Never "fix" such a route by removing it or by adding a sentence that points at it. Only repair real defects: wording that excludes the route (condition 1), or a test that fails correct fixes (condition 2). |



# I put it here myself. It needs improvising and relocating to its appropriate place. 
Move this section to just after §2 (the instruction rule), since that's where it belongs topically.

This is legal under the current rules, which only ban code names. But it is the opposite of the rule you're describing: the instruction lists the surfaces instead of stating the property once. So the honest wording is: "the instructions don't name the siblings, but they list each sibling's surface in product terms, which turns the task into a checklist." I'll correct this in the report.

fuck. that's why 30 out of 30 tasks are sovled in my scaled deepseek pipeline. dude, if you are gonna hand the agent a full list of surfaces, it becomes the checklist. we have to keep it a general rule and must not name surfaces. please make it a rule and a must have. it shoudl go in all 3 surfaces, screener, builder, hardening, fairness check and fairness fix but for now, since we are making a rules list, just make an md file named better patterns, and put this instruction there and all the 5 locations where we need to plant this in our pipeline.
also mention that thsi is the pattern that really makes the llm fail so making a pipeline without this pattern means nothing.

ok. these are the items blocked last time. nothing in here looks harmful. can you please try again to write this rules in better pattern.md file. for some reason, nothing looks problamatic to me here, mayby it was a misclassification..