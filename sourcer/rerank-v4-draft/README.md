# Host re-rank, version v4-draft (2026-10-16)

**Status:** draft. Not yet used to pick tasks, and not validated beyond the round-1 check below.

**What it is:** a re-ranking of the 1,462 candidate and shortlisted entries in `sourcer/index/`.
These are published, already-fixed OSV advisories. Each entry is scored as a HOST for a task,
using round-1 and round-2 lessons (`builder/BRIEF-trap-stack.md`), not as an advisory in
isolation. It is computed offline from the existing index. Nothing was downloaded, and the index
is unchanged.

**Files**
- `rerank.py`: the scoring script. Re-run it to regenerate the TSVs.
- `host-rank-all.tsv`: every entry, with its host rank and score, its v3 rank and score, and the
  reason for each point.
- `host-shortlist-40.tsv`: the top 40, with one entry per repo, at most 8 per language, and repos
  already built or trialled excluded.

**Scoring, in brief**
- **Plus:**
  - repo size from 20 MB to 1.5 GB (distance), or a fix that spans directories;
  - the same check at several sites, or an earlier fix that was bypassed;
  - name-based proxies for trap room (merged/default route, fallback, producer in another
    directory);
  - a weak wording proxy for a reason to dismiss;
  - weakness classes refitted to round 1 (access control and authentication up, saturated classes
    down).
- **Minus:** a single obvious sink, a one-site guard, a compact single-hunk fix, more than 4 fix
  commits, or a tiny or giant repo.
- **Fix size gets no points.**

**Check against round 1:** on the 6 mined round-1 bases the rank correlation is +0.77, against
+0.76 for v3. These are the bases v3 was fitted on, so this shows no loss, not validation. Only
12 of the top 40 overlap v3's top 40.

**Known limits**
- Repo size is known for only 498 of the 1,462 entries; the rest score 0 on size.
- The trap-room proxies fire broadly, so they need a reader or code pass before any build.
- Nothing in it targets MiMo specifically yet.

**Where it came from:** written by an Opus 5.5 sub-agent on 2026-10-16. Its task brief was cut off
before the stated goal, so it chose a read-only re-rank itself. The lead reviewed the output and
kept it as a draft.

**Next:**
1. A reader or code pass over the top 30.
2. Build from the confirmed ones.
3. Refit the weights on the outcomes and promote to v4.

## Screener tooling (added 2026-10-16)
For `builder/SCREENER-PROMPT-v1.md`. The prompt text and its output schema are read from that file,
never copied into these scripts.
- `validate_screen.py`: checks a screener record against the prompt's own JSON block (keys, types,
  enums, versions, no score field), resolves every file:line against the pinned tree (`--repo`), and
  warns where the `j` block or `pattern_fit` contradicts the observations.
- `screen-weights.json` (`screen-w0`, **not validated**): points per observation. Draft values from
  lessons-v1; not fitted, and not to be tuned on the calibration hosts.
- `rerank.py --screened DIR`: scores every valid record under DIR into `host-rank-screened.tsv`.
  `score_read` = observation terms + the weakness terms (H5). The base TSVs are unchanged (checked
  byte for byte against the committed output).
- `screen_prepare.py`: fills the prompt per (model, host) and writes the candidate JSON and
  `hosts.tsv`; `--calibration` takes the hosts from the prompt file's calibration table. The outcome
  labels go to `labels.tsv`, which stays local.
- `vm/fetch_hosts.sh`, `vm/run_screen.sh`: fetch each host's pinned tree, fix diff and latest
  release without `.git`; run one headless Claude Code screening with read-only file tools confined to
  the run dir and that host's code.
- `screen_calibrate.py`: the comparison-log metrics (field agreement with the reference, wrong
  evidence, ranking concordance with known outcomes, cost, time, stops).
