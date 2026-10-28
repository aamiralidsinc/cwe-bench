# Diversity population (experiment)

**Status:** set up 2026-10-27. 22 patterns and the chunk plan are agreed. Selection for chunk 1 has not started.

**Internal only.** Never copy this folder, or anything about it, to the client repo.

## What this experiment is for

Our breakers concentrate in a few patterns:
- 52% of trialled tasks are A01, Broken Access Control;
- path traversal is the most-built pattern and has the lowest yield (12%).

`reports/DIVERSITY-REMEDIATION-20261027.md` found two things:
- **Not a weakness of the patterns.** Rarer patterns fail both models at the same rate as the big ones (29% vs 26%).
- **A selection problem.** The batch is the top-N by score. The rarer patterns are 1–3% of the pool, so they get
  0–4 trials each.

This experiment replaces "top-N by score" with **a fixed quota per pattern** in each batch. It then measures two
things:
1. Does a quota batch produce breakers across more patterns (more OWASP categories, CWEs and mechanisms)?
2. What is the real yield of each pattern, once each one has enough trials to tell?

## Ground rules

1. **The main pipeline is not touched.** Nothing under `common/`, `pipelines/`, `sourcer/` or `build/audit/` is
   edited for this experiment.
2. **Copy before use.**
   - Any script, prompt or weights file needed from the main pipeline is copied into `copied/` first, and only the
     copy is run or changed.
   - Each copy is listed in `copied/SOURCES.md` with:
     - its original path;
     - the commit it was copied from;
     - what was changed.
3. **The candidate indexes are read-only.** Selection reads `sourcer/index/candidates.sqlite` (and the reserve index)
   in read-only mode, and writes its own outputs under `out/`.
4. **Task artefacts.**
   - Built tasks still go into the shared `build/<slug>` and `tasks/<slug>` folders, because the trial and audit
     tools read them from there.
   - They use the slug prefix `diversity-`, so they never collide with a main-pipeline slug.
   - This needs the owner's confirmation (see "Open questions").
5. **No double use.** A candidate is excluded if its advisory id or its repo was already built by any pipeline.
   This is the same rule as sibling2.

## Folders

| Folder | What goes in it |
|---|---|
| `copied/` | copies of main-pipeline files, plus `SOURCES.md` |
| `out/` | selection outputs, batch files, per-pattern tallies |
| `PATTERNS.md` (to write) | the pattern list: CWE sets, the "other places" hint for each pattern, and the quota |

## Patterns

**How the list was built:**
- It starts from the 30 mechanism families of the diversity report (section 3.3).
- **Merged:**
  - file upload goes into path traversal, as both are file confinement;
  - template injection goes into code injection, as both are code built from input.
- **A01 patterns are left out,** because the main pipeline keeps producing them. The exceptions are open redirect and
  CSRF, which each have only one breaker so far (owner, 2026-10-27).
- **Left out for now:** timing side channels (owner, 2026-10-27).
  - Wall-clock tests are noisy on a loaded VM.
  - Work-counting tests risk failing a correct fix that takes a different approach.
  - Supply is small.
- **Native code is added back** (owner, 2026-10-27): memory safety and integer overflow. C/C++ tasks already work:
  - tensorflow (8 CPU / 12 GB) and passenger (4 CPU / 8 GB) are both-model failures;
  - pillow (2 CPU / 4 GB) was solved by both.
  - **The cost:** a longer image build, recompiles after each agent edit, and ASan builds for the tests.
- **Also left out:** "other / unclassified" and, optionally, exceptional conditions (A10).
- **Result:** 22 patterns, 2 of them A01 (9%).

**Columns:**
- **Unbuilt repos in the pool:** repos with candidates in the in-window pool (P1, published from 2026-06-01) that no
  pipeline has built.
- **Screened, strong:** already screened (H4) with score ≥ 18, repo not built.
- **Older pool:** older advisories (P3), repo not built. These are not diff-checked yet.
- **New sources:** pending entries in the sources2 index (P2). These are not scored yet.

| # | Pattern | OWASP | Unbuilt repos in the pool | Screened, strong | Older pool | New sources | In-window pool can supply 12? |
|---|---|---|---|---|---|---|---|
| 1 | Open redirect | A01 | 15 | 1 | 193 | 63 | yes, just |
| 2 | CSRF / CORS / origin | A01 | 41 | 8 | 424 | 192 | yes |
| 3 | XSS / sanitiser | A05 | 77 | 5 | 1,848 | 684 | yes |
| 4 | SQL / NoSQL / query injection | A05 | 20 | 5 | 306 | 277 | yes |
| 5 | OS command / argument injection | A05 | 19 | 1 | 395 | 376 | yes |
| 6 | Code / template / expression injection | A05 | 49 | 6 | 466 | 351 | yes |
| 7 | Header / CRLF / log injection | A05 | 13 | 0 | 68 | 46 | just |
| 8 | XXE / XML entities | A02 | 5 | 0 | 186 | 24 | **no:** needs older advisories |
| 9 | Input validation / canonicalisation | A05/A06 | 69 | 4 | 707 | 374 | yes |
| 10 | Prototype pollution / mass assignment | A08 | 33 | 7 | 269 | 58 | yes |
| 11 | Authentication / session | A07 | 74 | 9 | 760 | 703 | yes |
| 12 | Signature / certificate verification | A04/A07/A08 | 39 | 5 | 355 | 298 | yes |
| 13 | Crypto misuse / weak randomness | A04 | 22 | 1 | 303 | 116 | yes |
| 14 | Secrets in logs or errors | A09 | 17 | 2 | 220 | 90 | yes |
| 15 | Deserialization | A08 | 11 | 5 | 259 | 120 | **no:** needs older advisories |
| 16 | Supply chain / untrusted code loading | A03 | 7 | 2 | 77 | 81 | **no:** needs older advisories or new sources |
| 17 | Request smuggling / parser differential | A06 | 16 | 3 | 108 | 64 | yes |
| 18 | Race / TOCTOU | A06 | 12 | 1 | 128 | 124 | just |
| 19 | ReDoS | unmapped | 30 | 0 (the screener skips DoS) | 197 | 45 | yes |
| 20 | Algorithmic / resource-exhaustion DoS | unmapped | 156 | 3 | 922 | 848 | yes |
| 21 | Memory safety (native) | unmapped | 41 | 1 | 455 | 1,377 | yes (new sources are mostly C/C++) |
| 22 | Integer overflow / numeric | unmapped | 15 | 0 | 100 | 267 | just |

**Superseded for supply.** The supply columns above describe the main pipeline's pool and are kept for comparison
only. The experiment now draws on its own sources; see "Sources: separate from the main pipeline".

**What "yes" means:** "yes" counts repos, not buildable tasks. Every pattern has 9 or fewer strong screened
candidates, so all of them need more screening (see "Screening need").

## Sources: separate from the main pipeline

**Decided by the owner, 2026-10-27.** The experiment draws on two slices the main pipeline never reads. They are
recorded as D1 and D2 in `docs/sources_and_usage.md`.

**The slices:**
- **D1:** older advisories already in the main index (status `deferred`), published 2025-01-01 to 2026-05-31. They
  were downloaded with the OSV dumps but set aside by the sourcer's window (published from 2026-06-01). Nothing new
  needs downloading.
- **D2:** the new sources (sources2: GitHub unreviewed, OSV GIT, NuGet), published from 2025-01-01.
- **Repos are kept apart too.** Any repo with a candidate in the main pool, or built by any pipeline, is excluded.

**Order of use:**
1. D1 from 2025-07 onwards (newest first, which lowers the chance the models memorised the fix);
2. the rest of D1 (2025-01 to 2025-06);
3. D2.

Go before 2025 only for a pattern that still cannot fill its quota.

**Supply per pattern** (distinct repos, after the exclusions):

| Pattern | D1 2025-07 to 2026-05 | D1 2025-01 to 2026-05 | D2 2025 onwards |
|---|---|---|---|
| Open redirect | 27 | 31 | 91 |
| CSRF / CORS / origin | 31 | 48 | 182 |
| XSS / sanitiser | 134 | 188 | 603 |
| SQL / NoSQL / query injection | 40 | 50 | 246 |
| OS command / argument injection | 74 | 90 | 330 |
| Code / template / expression injection | 74 | 93 | 313 |
| Header / CRLF / log injection | 8 | 11 | 62 |
| XXE / XML entities | 12 | 19 | 34 |
| Input validation / canonicalisation | 99 | 120 | 337 |
| Prototype pollution / mass assignment | 40 | 54 | 56 |
| Authentication / session | 109 | 145 | 537 |
| Signature / certificate verification | 69 | 90 | 222 |
| Crypto misuse / weak randomness | 43 | 53 | 167 |
| Secrets in logs or errors | 23 | 34 | 94 |
| Deserialization | 29 | 47 | 133 |
| Supply chain / untrusted code loading | 20 | 28 | 120 |
| Request smuggling / parser differential | 12 | 18 | 44 |
| Race / TOCTOU | 21 | 27 | 119 |
| ReDoS | 15 | 27 | 38 |
| Algorithmic / resource-exhaustion DoS | 130 | 167 | 410 |
| Memory safety (native) | 78 | 91 | 576 |
| Integer overflow / numeric | 23 | 27 | 237 |

**Work before chunk 1:** none of these entries have fetched diffs or scores yet. On a copy of the index in this
folder, run the copied sourcer's stages for D1 and D2 only, in this order: `diffs`, `classify`, `parents`,
`repo-meta`. Then run the copied screener.

**Watch the effect of age.** Older advisories are more likely to be memorised by the models. Record each task's
publication date, and compare yield for 2025-H1, 2025-H2 and 2026 after chunk 1.

## Source pool (built 2026-10-27)

**What it is:** the newest 50 distinct unbuilt repos per pattern, in reverse chronological order. These are taken
before any scoring or screening, so the later filters have room to reject.

**How to rebuild it:**
`python3 -I diversity_population/build_source_pool.py --built diversity_population/out/built_repos_20261027.txt`

**Output:** `out/source_pool.sqlite`, with three tables:
- `pool`: one row per (pattern, repo);
- `pattern_depth`: how far back each pattern's list goes;
- `meta`: how the pool was built.

**The date used for ordering:**
- The fix-commit date where it is known, otherwise the advisory's published date.
- **Why:** about 5% of new-source records are old bugs with a new CVE. For example, a 2017 Discourse bug was
  published in October 2026.
- **Coverage now:** 525 of the 1,100 rows have a fix date. The diffs stage fills in the rest, and may reorder the
  lists.

**Result:**
- **Size:** 1,100 rows over 738 distinct repos. A repo can sit in up to 3 patterns, and each repo is used once at
  selection time.
- **Source:** 1,036 rows (94%) come from the new sources, because they are the newest data.
- **Depth:** 14 of the 22 patterns reach 50 repos without going back before June 2026.
- **Outliers:** XXE goes back to 2025-03, ReDoS to 2025-06 and request smuggling to 2025-08.
- **Chart:** a private chart page, https://claude.ai/artifact/CwVXxi7wDTCVaxQZdVv2Lj

## Steps 1–4 on the pool (started 2026-10-28 00:18Z)

**Decision (owner, 2026-10-27):**
- No date cut-off: all 50 per pattern go through steps 1–4.
- Reason: if the screener or scorer later rejects too many, the steps do not have to be rerun on more entries.

**How it runs:**
- **Code:** the copied sourcer (`copied/sourcer/`).
- **Index:** `out/index/candidates.sqlite`, a copy of the sources2 index.
- **Downloads:** `~/.tb-graders/cwe/diversity-data/`.

**Preparation:**
- `prepare_index.py` sets the 1,066 pool entries to `pending` and every other entry to `deferred`. Original statuses
  are kept in the table `div_original_status`.
- It also reuses 4,395 cached patches from the sources2 and main data folders.

**The steps** (`run_steps.sh`; resumable):

| Order | Step | Notes |
|---|---|---|
| 1 | diffs | |
| 2 | classify | |
| 3 | diffs again | for fix commits that classify moved to a pool entry |
| 4 | classify again | |
| 5 | parents | |
| 6 | repo-meta | 55 repos per hour (GitHub's unauthenticated limit), so it takes several hours |

**Progress:**
- `out/steps_status.txt` holds the current stage, with a heartbeat every 30 s.
- `out/steps.log` holds the stage output.

**GitHub token:** none is used. The `gh` CLI on this Mac is logged in to an account that is not the owner's.

**What classify rejects:**
- the copied sourcer's default filters, unchanged;
- in particular, a fix commit more than 365 days older than its advisory. This catches old bugs that only recently
  got a CVE.

Rejected entries stay in the index with their reason.

**Result (finished 2026-10-28 ~00:50Z):**
- **Steps 1–3:** classify kept 657 of 1,066 entries; parents resolved 656 of 657.
- **Step 4 (repo-meta):** done with a GitHub token (`AAMIR_ALI_DSINC_GH` in `/Users/dev/terminal-bench/.env`, read
  from the environment, never printed) in about 3 minutes, instead of 10 hours unauthenticated. The token is used
  by the copied sourcer only.
- **Classify was re-run with the repo stars known.** Its existing filter dropped 58 entries from repos under
  25 stars.
- **Now:** 599 candidates, 467 rejected.
- **Candidates per pattern:** from 18 (algorithmic DoS) to 35 (prototype pollution).
- **Size:** 19 candidates sit in repos over 1.5 GB, which the screener skips.
- **Main reject reasons:**
  - duplicate fix commit (129);
  - no source change, or docs, manifest or config only (about 200);
  - low-adoption repos (58);
  - patches over 3 MB (32);
  - not buildable on plain Linux (20).

## Screener (started 2026-10-28 01:05Z)

**Decisions (owner, 2026-10-27):**
- **Recipe:** the sibling-injection recipe.
- **Selection:** one selection run picks 12 per pattern (264 in all); it is split into chunks later.
- **Coverage:** to pick 12 per pattern, the screener runs once on every candidate.

**Jobs:**
- `make_screener_jobs.py` writes `out/screener_jobs.jsonl`: 581 jobs over 459 repos.
- The jobs are the 599 classify candidates, minus 18 in repos over 1.5 GB.
- Jobs per pattern: from 18 (input validation, algorithmic DoS) to 34 (prototype pollution).
- The list is round-robin over the patterns, so a partial run covers every pattern.

**The screener:** `copied/screener/run_screener.py` with `copied/screener/SCREENER-PROMPT-v2.md` (Opus 5.5).
- **Run from the Mac,** so the VM pipeline is not loaded.
- **The prompt is unchanged** except for one input line: the pattern's "where sibling sites usually are" hint from
  `patterns.json`, marked as a pointer and not as evidence.
- **The DoS skip does not apply.** It lives only in the picking step, which is not used here.
- **Disk:** the Mac has about 24 GB free, so each checkout is deleted when its job ends.

**Test job:** diversity-81529 took 132 s, cost $0.65 and wrote a valid record.

**Full run:**
- 5 jobs in parallel; about $380 and 5–8 h expected.
- **Records:** `out/screener/<entry_id>.json`.
- **Log:** `out/screener/_run.log`.
- **Resumable:** jobs with a record are skipped.

**Moved to the VM (owner, 2026-10-28 01:17Z):**
- **Why:** the Mac run was paused at 23 records to run 50 in parallel on klavis-vm.
- **Where:** the VM run lives only in `~/diversity_population/` (separate from `~/cwe-bench`):
  - code in `copied/screener/`;
  - records in `out/screener/`;
  - checkouts in `work/`, deleted per job (`DIV_WORK`).
- **VM test job:** diversity-83645 took 204 s, cost $1.27 and wrote a valid record.
- **Full run:** 50 in parallel, 6 s stagger. Expected time: about 581 × 3–4 min ÷ 50, roughly 45–60 min.

**Next: selection, 12 per pattern.**
1. Rank each pattern's screened candidates with a copy of the sibling ranker (`pipelines/sibling/3-rank/rerank.py`).
2. Pick with a copy of DeepSeek select (`pipelines/sibling/4-select/`), run within each pattern.
3. Take the union, as sibling2 did.
4. Use each repo once.

## Selection (finished 2026-10-28 ~02:12Z)

**How it ran:**
- **Where:** `select_per_pattern.py` on the VM (`~/diversity_population`), using the copies only.
- **Rerank:** `rerank.py --screened` scored all 581 records.
- **DeepSeek:** each pattern's pool went through DeepSeek select **3 times** (owner, 2026-10-28: the latest pipeline
  uses 3 passes). All 66 calls ran at once; 2 failed once and succeeded on retry.
- **Merging:** `combine.py` merged the passes.

**Order within a pattern:** the mean of the combined DeepSeek rank and the rerank rank.

**Assignment:**
- Scarcest pattern first.
- Each repo is used once.

**Result:** `out/selection/selected.tsv`.
- **Size:** 264 tasks, 12 per pattern for all 22 patterns, over 264 distinct repos.
- **Rerank-only picks:** 12 of the 264 were picked by no DeepSeek pass and came in on the rerank rank. They are 1–2
  each in crypto, deserialization, header injection, integer overflow, memory safety, prototype pollution, race,
  secrets in logs and XXE.
- **Lowest mean rerank score:** algorithmic DoS (10.5), memory safety (12.2), ReDoS (12.5) and SQL (13.2).
- **Languages:** PHP 40, Python 27, TypeScript 25, C 22, Java 20, Go 17, Rust 10, Elixir 10, C++ 10, C# 7, Ruby 6,
  JavaScript 2.

**Next:** split the 264 into chunks, then build with the sibling recipe.

## Top-up of the 6 weak-tailed patterns (finished 2026-10-28 02:52Z)

**Decision (owner, 2026-10-28):**
- **Which patterns:** the 6 with 3 or more picks below the median score (12): memory safety, algorithmic DoS,
  ReDoS, SQL, deserialization and input validation.
- **What:** take 50 more, older, candidates each, and replace the weak picks.
- **When to build:** nothing starts until the list is final.

**Steps:**
1. **Pool:** `build_source_pool.py --per-pattern 250`, then the next 50 new repos per pattern
   (`out/source_pool_ext.sqlite`; 300 entries over 300 repos, none already in the pool).
   - ReDoS reaches back to 2023-02; the others to 2025-11 through 2026-08.
2. **Steps 1–4:** `extend_index.py`, then `run_topup.sh`. 188 of the 300 are candidates; 184 were screened (4 are in
   repos over 1.5 GB). The screener ran on the VM, 50 in parallel, with 0 failures.
3. **Replacement:** `topup_replace.py`.
   - Re-rank everything, then run DeepSeek 3 passes on each of the 6 expanded pools.
   - Keep picks scoring 12 or more; fill the freed slots in the same order as the first selection, taking only
     candidates scoring 12 or more.
   - The other 16 patterns are unchanged.

**Result:** `out/selection/selected_v2.tsv` (changes in `topup_changes.tsv`).
- **Size:** 264 tasks, 12 per pattern, 264 distinct repos.
- **Replaced:** 23 picks.
- **Median score in the 6 patterns, before and after:**

  | Pattern | Before | After |
  |---|---|---|
  | Memory safety | 13 | 17 |
  | Algorithmic DoS | 13.5 | 16 |
  | ReDoS | 13.5 | 15 |
  | SQL | 13.5 | 16.5 |
  | Deserialization | 15.5 | 18 |
  | Input validation | 15 | 18 |

- **Weak picks left:** ReDoS keeps 3 picks below 12. Even the top-up had too few strong ones, and every ReDoS
  candidate carries the screener weights' −3 DoS penalty.
- **Overall:** median 16; 15 of the 264 score below 12 (3 in ReDoS, and 1–2 each in patterns that were not topped
  up).

## Chunks (2026-10-28)

**Decisions (owner, 2026-10-28):** the other 12 weak picks stay. The chunks follow candidate score (best first), not
category.

**Files:** `out/chunks/chunk1.tsv` … `chunk4.tsv`, plus `all_chunks.tsv` (also on the VM).

**How:**
- 4 chunks of 66.
- The 264 are sorted by score_read, as it is, including the DoS penalty; ties go to the DeepSeek score.
- Each row has a proposed slug, `diversity-<repo name>`. None of them clashes with the VM's `build/` or `tasks/`.

| Chunk | Score range | Patterns covered |
|---|---|---|
| 1 | 23–19 | 19 (no ReDoS, algorithmic DoS or integer overflow; the first two lose 3 points to the DoS penalty) |
| 2 | 19–16 | 21 |
| 3 | 16–14 | 21 |
| 4 | 14–7 | 21 |

**Nothing is built yet.**

## Running off the VM: GitHub Actions reference (2026-10-28)

**Why:** the VM is busy with the scale run.

**What exists:** `actions/README.md` documents how precision_validation built and trialled on GitHub Actions, with
the problems it hit and the open risk questions. `actions/reference/` holds unchanged copies of its workflows and
scripts. Nothing has been run.

## Quota and chunks

**Target:**
- **12 builds per pattern:** 22 × 12 = 264 builds.
- **Expected yield:** about 10% breakers per build. That is about 50% of builds reaching a graded trial, times about
  25% of graded tasks that fail both models.
- **That gives** about 1 breaker per pattern. The chance that a pattern with a true 10% yield shows zero breakers in
  12 builds is about 28%, so one empty pattern is not proof that the pattern is weak.

**Four chunks of 66** (3 per pattern):
- 66 fits the 60-slot pool, because slots refill as builds finish.
- **Chunks 1 and 2:** a fixed quota of 3 per pattern (6 per pattern in total). They are chosen together.
- **Chunks 3 and 4:** re-allocated from the chunk 1–2 results, in this order:
  1. **Gate losses:** a pattern that loses most builds at the gate gets fewer slots until the cause is fixed.
  2. **Signal:** a pattern with any model failure (one or both models) keeps its 3.
  3. **Easy solves:** a pattern whose graded tasks were all solved by both models drops to 1–2. Its freed slots go
     to the patterns with signal.
- **The pattern total stays near 12.** It can range from 8 to 16.

**Filling a pattern's quota, in this order:**
1. strong screened candidates of that pattern;
2. unscreened in-window candidates (screen them first);
3. older advisories, then new sources.

**If a pattern still cannot fill its quota,** the slot goes to the pattern with the most usable supply. It is never
given to an A01 pattern other than open redirect or CSRF.

**Exclusions:** one task per repo. Repos built by any pipeline are excluded.

**The 71 gate-passed tasks** sent to trial on 2026-10-27 count towards the per-pattern yield tally, not towards the
quota.

**Screening need:**
- To pick 12 strong candidates per pattern, we need about 25–30 screened candidates per pattern.
- That is about 400–500 new Opus screener runs, at about $0.75 each: roughly $300–375.
- These are screened in batches, one pattern block at a time, before each chunk.

## Open questions for the owner

1. ~~Choose the quota and batch size.~~ Decided 2026-10-27: 22 patterns, 12 builds per pattern, 4 chunks of 66.
2. Confirm the `diversity-` slug prefix and the use of the shared `build/` and `tasks/` folders.
3. ~~Confirm the ReDoS exception.~~ Allowed 2026-10-27. ReDoS candidates are screened in the copy of the screener
   only; the main screener's DoS exclusion is unchanged.
