# Stacking pipeline (Phase 1 tooling), 2026-10-22

**Design:** `../STACKING-EXPLORATION.md`.

**Phase 1 runs locally and needs no VM.** Phase 2, building and trialling tasks, needs a VM with
Docker.

| Step | File | What it does | Status |
|---|---|---|---|
| 1a | `h4_rank.py` | ranks the screened hosts for H4 stacking (several real routes of different kinds; at least one DeepSeek-type and one MiMo-type) → `out/h4_candidates.tsv`, `out/h4_shortlist.md` | done: 150 records, 9 unbuilt hosts offer both types |
| 1b | `h3b_pairs.py` | resolves "incomplete fix / bypass / regression of CVE-…" advisory pairs to repo and fix commits → `out/h3b_pairs.tsv`, `out/h3b_summary.md` | done: 455 pairs, **148 ready**, 23 dropped as same-fix-commit |
| 1c | `szz_pairs.py` | SZZ check of each ready pair: does the later fix change code the earlier fix wrote? (H3a regression vs H3b incomplete) → `out/szz_pairs.tsv`, progress in `out/szz_run.log` | running (resumable); blobless clones in `~/.tb-graders/cwe/stacking/clones/` |
| 1d | `h12_groups.py` | co-present advisories per package, split by fixed together (H1) or separately (H2) → `out/h12_groups.tsv`, `out/h12_summary.md` | done: 916 mid-size groups (H2 652, mixed 213, H1 51) |
| 2 | `STACKING-READER-PROMPT.md` | per candidate: traps with mechanism, locations, tier per model, type; shared-guard groups; history; conflicts; fairness risks; chosen design → `out/reader/<id>.json` | written; not run yet |
| 3 | `score_stack.py` + `../sourcer/stacking_weights.json` | probabilistic score on D1-D3, plus flags (missing DeepSeek-type or MiMo-type trap, single concept, single trap carries, fairness risk) → `out/stack_scores.*` | done; passes the calibration check (`calibration/`: sib2 0.59 > sib 0.02 > prompty 0.008, flags match) |
| 4 | `STACKING-BUILD-ADDENDUM.md` | the stacking rules appended to the build prompt: 3+ independent concepts, both model types, no single carry, history rules (H3 pin and first-fix check, masking, conflicting fixes, dependency bumps), recall check, a one-bug control task | written |
| 5 | `check_stack.py` | static conformance check of a built stacked task (manifest `stacking` block, concepts, types, per-concept wrong-fix patches, recall patches, coupled tests, control task) | done; tested on good and bad manifests |

**Also in Phase 1:**
- **Step 2 runners:** `make_reader_jobs.py` builds `out/reader_jobs.jsonl`; `run_reader.py` runs
  the reader on it (see "Running the reader" below).
- **`STACKING-FAIRNESS-ADDENDUM.md`:** the coupled, shape, fixture, independence, history, contract
  and decisive-test checks for stacked tasks, plus the fairfix rules. It is appended to the fairness
  brief and the fairfix prompt when a manifest has a `stacking` block. The Phase 2 launchers must do
  this; it is not wired yet.

**Decisions (2026-10-22):**
- **Phase 2 builder model: DeepSeek V4.1 Flash**, via the VM's `drive.sh deepseek`.
- DeepSeek-built tasks used to describe sibling surfaces in their instructions. The template rules
  (`BETTER-PATTERNS.md` §2), the addendum, `check_stack.py` and fairness step 3a are the guards
  against that.
- The reader (step 2) runs locally with Claude Code.

## Running the reader (step 2)

1. Build the job list (re-run it after the SZZ miner finishes, so its results order the H3 pairs):

       python3 -I stacking/make_reader_jobs.py --h4 9 --h3 12

2. Optional dry run: clones, pins, worktrees and filled prompts, with no model call:

       CLAUDE_BIN=/Users/dev/.nvm/versions/node/v24.19.0/bin/claude python3 -I stacking/run_reader.py --dry-run

3. Run it, in a plain terminal (not inside a chat):

       CLAUDE_BIN=/Users/dev/.nvm/versions/node/v24.19.0/bin/claude python3 -I stacking/run_reader.py --parallel 3 --model claude-opus-5-5

**Outputs:** `stacking/out/reader/<id>.json` (one per candidate), `<id>.run.json` (the CLI's own
output) and `_run.log` (progress: one start and one finish line per job). Jobs that already have an
output are skipped, so re-running resumes.

4. Score: `python3 -I stacking/score_stack.py`, giving `stacking/out/stack_scores.md`.

**Run, in order:**
1. `h4_rank.py --built <tasks dirs>`, `h3b_pairs.py`, `szz_pairs.py`, `h12_groups.py`;
2. the reader prompt on the shortlists;
3. `score_stack.py`;
4. build with the build prompt plus the addendum;
5. `check_stack.py SLUG`, then `builder/gate.py SLUG`.

**Notes:**
- The SZZ attribution is weak when a later fix only adds code: those rows are `add-only`, and need
  reading by hand.
- The H4 test for "the protection never existed" is a text heuristic over the screener records. The
  reader (step 2) confirms it against the code.
