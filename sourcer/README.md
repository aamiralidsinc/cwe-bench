# cwe-bench sourcer

Finds real security fixes that could become "fix the vulnerability" benchmark tasks, and
keeps one persistent index of every record any sourcer has looked at.

Sourcer 1 (`osv_sourcer.py`, sourcer name `osv`) mines the public OSV bulk dumps.
Later sourcers (seeded search, direct scans of GitHub history) should import `index_db.py`
and `patchmetrics.py` and write to the same index.

Python 3.9+, standard library only. No Docker, no GitHub token, no `gh`.

## Files

| Path | What |
|---|---|
| `osv_sourcer.py` | the sourcer: all stages, one sub-command each |
| `index_db.py` | the shared index (schema, "have we seen this" lookups, TSV export) |
| `patchmetrics.py` | `.patch` parser, file classifier, fix-shape metrics |
| `index/candidates.sqlite` | the index (source of truth) |
| `index/candidates.tsv` | flat export of the `entries` table, rewritten after every stage |
| `review/annotations.tsv` | reading notes: keep/skip/drop, role (main/control), the JUDGEMENT columns and the guessed fields |
| `review/make_annotations.py` | the script the first round's notes were written with (edit the TSV or this, not both) |
| `review/proposed.tsv` | last automatic proposal |
| `shortlist-20.tsv`, `shortlist-20.md` | the shortlist (16 main + 4 controls), written by `finalise` |

Downloads (dumps, cached patches, cached commit pages, repo metadata) are untrusted and live
outside this directory in `~/.tb-graders/cwe/sourcer-data/` (`--data` to change). The
sourcer refuses a data directory inside the code directory. Downloaded bytes are only parsed
as JSON or text; nothing from them is executed.

## How to run

Always run with `-I` (isolated mode: ignores environment variables and the current directory):

```sh
cd /Users/dev/terminal-bench/cwe-bench/sourcer
python3 -I osv_sourcer.py fetch-dumps                 # 7 ecosystem zips, about 300 MB
python3 -I osv_sourcer.py parse --since 2026-06-01    # stages 1-2
python3 -I osv_sourcer.py diffs --delay 0.6           # stage 3, long; stop (Ctrl-C) and resume freely
python3 -I osv_sourcer.py classify                    # stages 4-5, no network
python3 -I osv_sourcer.py repo-meta --limit 55        # optional, see below
python3 -I osv_sourcer.py classify                    # again, to apply stars / size
python3 -I osv_sourcer.py parents --limit 60          # vulnerable commit for the best candidates
python3 -I osv_sourcer.py propose                     # 16 + 4 controls -> review/proposed.tsv
python3 -I osv_sourcer.py show GHSA-xxxx-xxxx-xxxx    # read advisory + fix diff
#   ... write keep/skip/drop rows with the judgement columns in review/annotations.tsv
python3 -I osv_sourcer.py classify                    # copies the judgement into the index, score_read
python3 -I osv_sourcer.py finalise                    # shortlist-20.tsv / .md, index status
python3 -I osv_sourcer.py stats                       # funnel and per-signal pool counts
```

After changing `patchmetrics.py` or the advisory text rules, recompute without any network:

```sh
python3 -I osv_sourcer.py remetrics    # re-parse every cached patch
python3 -I osv_sourcer.py resignal     # re-read advisory text from the dumps
python3 -I osv_sourcer.py classify
```

Every stage is incremental:

- `parse` skips any advisory whose id or alias is already in the index.
- `diffs` skips any commit that already has a `fetch_status`; patches are cached on disk, so
  even a deleted index does not cause a re-download. `--retry-errors` retries network errors.
- `classify` re-evaluates entries that are pending, candidate, shortlisted or rejected at
  the diff stage; it never touches parse-stage rejections or manual drops.
- Widening the recency window is `parse --since 2026-01-01`: it promotes `deferred` entries
  to `pending`; then run `diffs` and `classify` again.
- Refreshing the dumps is `fetch-dumps --force` then `parse`: only new advisories are added.

## Stages

1. **parse**. Reads every record in every dump. `MAL-*` (malware) records are skipped by
   file name and only counted. All other records are grouped by id and aliases (so the GHSA,
   CVE, PYSEC, GO and RUSTSEC copies of one vulnerability become one entry; the GHSA copy
   supplies CWE ids and severity). An entry is kept when it is not withdrawn, has at least
   one CWE id, and has a GitHub repository with at least one fix commit SHA, taken from
   reference URLs of the form `github.com/<owner>/<repo>/commit/<sha>` or
   `/pull/<n>/commits/<sha>`, and from `affected[].ranges` of type `GIT` (`fixed` events).
   When commits point at more than one repository, the one with most commits wins.
   Everything else is recorded as rejected with one of: `withdrawn`, `no_cwe`,
   `no_github_repo`, `no_fix_commit`, `no_fix_commit_pr_only` (a pull request is referenced
   but no commit; a later sourcer could resolve these).
2. **recency** (inside `parse`). Entries published before `--since` get status `deferred`
   with reason `outside_recency_window`. They are not inspected until the window is widened.
   The published date is the earliest of the aliased records. The fix commit's own date is
   stored later as `fix_commit_date`.
3. **diffs**. For each pending entry, fetches up to `--max-commits` (default 3) fix commits
   from `https://github.com/<owner>/<repo>/commit/<sha>.patch` (the plain web URL, no API,
   no credentials), one request at a time, `--delay` seconds apart, with a descriptive
   User-Agent. On HTTP 429 it honours `Retry-After` (30 s minimum, three retries) and then
   stops the stage; nothing is done to get round a limit. Patches over 3 MB are not kept
   (`too_large`). The queue is ordered by an advisory-only pre-score (favoured weakness
   class, Java/Rust then Go/Ruby/PHP ecosystems, wording that points at signals 1-4), then
   newest first, so an interrupted run has covered the most promising entries. Per-commit
   metrics go to the `commits` table: non-blank added / removed lines in non-test source
   files, source files, hunks, test files, other files, dominant language, and the fix-shape
   JSON described under "Computed signals".
4. **classify: reject**. Reasons recorded:
   - `fix_commit_unavailable(...)`: 404 or fetch error for every fetched commit
   - `dependency_or_manifest_only`, `docs_only`, `tests_only`, `manifest_config_docs_only`,
     `no_source_change(...)`: no non-test source file changed
   - `enormous_refactor(...)`: more than `--max-lines` (1500) changed source lines, or a
     patch over 3 MB. This cap is the only use of fix size.
   - `stale_fix_commit(dated ...)`: the fix commit is more than `--max-fix-age-days` (365)
     older than the advisory; `no_recent_source_commit(...)`: the only source-changing
     commits referenced are over 120 days older than the newest referenced commit (an
     advisory sometimes links the commit that introduced the flaw)
   - `not_plain_linux_docker:<kind>`: keyword rules on repo name, package name and advisory
     summary for `kernel`, `firmware_or_embedded`, `mobile_app`, `browser_extension`,
     `desktop_gui`, `gpu_only`, `windows_only`, `macos_only`, `hardware`; plus Swift,
     Objective-C or Dart as the dominant language
   - `toy_or_demo_repo(name)`: repo name contains demo, example, sample, tutorial,
     playground, poc, ctf, vulnerable, ...
   - `toy_or_low_adoption(stars=N)`: fewer than `--min-stars` (25) stars; only known for
     repositories `repo-meta` has looked up
     (archived / fork flags are recorded in `repo_flags` and `notes`, not used to reject)
   - `duplicate_fix_commit_of_entry_<id>`: every fix commit already belongs to an earlier
     entry (several advisories fixed by one commit); the earlier entry carries the analysis
   - `manual:<note>`: dropped by the reviewer after reading (`finalise` writes these)
5. **classify: score**. See "Scoring rule". When an entry has several fetched fix commits
   (backports to several branches, or a fix in several parts) the metrics and the score
   describe the one with the largest in-range source change; `notes` says so.
6. **propose / show / finalise**. `propose` suggests 16 main candidates by score (one per
   repository, at most 4 per primary CWE, language quota
   `Java=3,Rust=2,Go=4,PHP=2,Ruby=1,C/C++=1,Python=3,JS/TS=3`, and Python or JS/TS only when
   at least three of signals 1-5 are computed present) plus 4 controls (Python or JS/TS,
   single compact hunk, single sink or one-site guard, no multi-site, no bypass, no favoured
   class, lowest score first). It is a proposal: the reviewer reads each one with `show`
   and records the verdict, role and judgement in `review/annotations.tsv`. `finalise`
   writes the shortlist from the kept annotations and sets index status and `shortlist_role`
   (`manual:<note>` rejection for drops; `skip` rows stay candidates for later rounds).

Optional lookups, both bounded and cached:

- **parents** fetches the ordinary commit web page
  (`https://github.com/<owner>/<repo>/commit/<sha>`) for the top `--limit` candidates and
  reads the full SHA and the first parent from the JSON embedded in it. `.patch` does not
  contain the parent, and for a merge commit its first line is not the commit itself.
- **repo-meta** asks `https://api.github.com/repos/<owner>/<repo>` without credentials for
  stars, size and archived/fork flags, for at most 55 repositories per run (the
  unauthenticated limit is 60 per hour) and stops when the limit header is nearly used.
  This is the only use of the API; it is not needed for any other stage.

## Scoring rule (version 2)

Fix size is not a difficulty signal. The score rewards the properties that make a correct
fix hard to find, each stored in its own index column so it can later be tested against
model results. Columns named `c_*` are computed from the fix diff and the advisory text.
Columns named `j_*` are a reader's JUDGEMENT, filled only for entries someone has read.

Two scores are stored: `score` uses computed columns only and is comparable across the whole
pool; `score_read` replaces the proxies for signals 1, 2, 3 and 7 with the reader's verdict
(a "no" scores 0 even where the proxy fired). `score_detail` lists every term.

| # | Signal | Computed column and points | With JUDGEMENT |
|---|---|---|---|
| 1 | Multi-site trust decision: the same check has to hold at several sites | `c_same_check_sites` >= 3: +5; = 2: +3; else `c_multi_site` (4+ code hunks in 2+ files): +2; else advisory wording about sibling sites: +1 | `j_multi_site`: +5 |
| 2 | Cause in a different layer from the symptom | `c_cause_layer_hint` (advisory wording only): +2 | `j_cause_other_layer`: +4 |
| 3 | A defence was present and did not work | `c_defence_present` (advisory says a defence failed AND the fix rewrote a condition): +3; wording only: +1 | `j_defence_ineffective`: +4 |
| 4 | Bypass / incomplete earlier fix; repeated advisories | `c_bypass_incomplete`: +3; `c_sibling_advisories` >= 3: +2, 1-2: +1 | same |
| 5 | Weakness class: authentication and session, authorisation, integrity, logic / insecure design | `c_favoured_class`: +3 (`c_class` names the class) | same |
| 6 | Fix shape | 3+ code hunks that are far apart (`c_far_apart`): +2; `c_restructured`: +1; `c_single_compact_hunk`: -3 | same |
| 7 | The obvious over-broad repair would break legitimate, covered use | not computable | `j_overbroad_breaks_legit`: +2 |
| LOW | Single obvious sink fixed at one spot | `c_single_sink`: -3 | same |
| LOW | One-site added-only guard | `c_one_site_guard`: -2 | same |
| LOW | Compact fix in a small repository (under 20 MB; only when `repo-meta` knows the size) | `c_compact_small_repo`: -1 | same |
| | Build risk: repository over 1.5 GB (when known) | -1 | same |

Not scored: total changed lines, severity, tests in the fix (recorded as `tests_in_fix`,
used only as a tie-break in `propose`), language (handled by the quota; `lang_tier` records
weakest = Java/Kotlin/Scala/Rust, weak = Go/Ruby/PHP/C/C++, strong = JS/TS, python).

### Computed signals: how each is derived

From `patchmetrics.shape_metrics` over the non-test source part of the fix commit:

- `c_fix_sites`: hunks that change real code (hunks touching only imports or comments are
  not counted); `c_site_files`: files holding them.
- `c_same_check_sites`, `c_same_check_name`: the largest number of fix sites that all gained
  a call to one same function which no removed line called, and that function's name. The
  defining site is not counted. Example: `safeJoinModulesDir` added at 4 path joins.
- `c_multi_site` = `c_same_check_sites` >= 2, or 4+ fix sites in 2+ files.
- `c_modified_check_lines`: removed lines that look like a condition, validator or sanitiser.
- `c_defence_present` = advisory wording that a defence failed (or an incomplete fix) AND
  `c_modified_check_lines` >= 1.
- `c_single_compact_hunk` = one fix site, or one file with at most two sites within 30 lines.
- `c_far_apart` = sites in 2+ files, or more than 80 lines apart in one file.
- `c_restructured` = at least 5 removed code lines and at least 20% of changed lines removed.
- `c_one_site_guard` = compact and at most 2 removed lines (added-only guard).
- `c_single_sink` = a sink-class CWE (command, SQL, code, template, XSS, header injection)
  with no favoured class, fix in one file, and no repeated check.

From the advisory text (regular expressions in `osv_sourcer.py`, stored in `adv_signals`):
`fix_bypass` (signal 4), `multi_site_text`, `cause_layer_text`, `defence_text`.

From CWE ids: `c_class` (`auth_session`, `authz`, `integrity`, `logic_design`, `other`; the
CWE sets are `CLASS_CWES` in `osv_sourcer.py`), `c_favoured_class`.

Known weaknesses: `c_cause_layer_hint` is wording only (it fired on 24% of the first run's
pool) and carries little information without a reading. `c_multi_site` is broad (55% of the
pool); `c_same_check_sites >= 3` (22%) is the sharper form, but it misses a check that is
inlined rather than called, or a call that replaced an older call of the same name, and it
also fires when a renamed function is simply called from several places (in the first
shortlist the reader disagreed with the computed value on 3 of 16 for signal 1, 8 of 16 for
signal 2 and 6 of 16 for signal 3). The class comes from the advisory's CWE labels, which are sometimes wrong or generic.
All metrics describe one commit. Nothing measures build time unless `repo-meta` has run.

### Judgement columns (from `review/annotations.tsv`)

`j_read`, `j_multi_site`, `j_sites_touched`, `j_sibling_sites` (yes / no / unknown),
`j_cause_other_layer`, `j_defence_ineffective`, `j_overbroad_breaks_legit`,
`j_tempting_wrong_fix`. `classify` copies them into the index and computes `score_read`.
For a main shortlist row the "why hard" text must name which of signals 1-3 applies and the
tempting wrong fix; a candidate for which no tempting wrong fix can be named is not kept.

## Index schema (`index/candidates.sqlite`)

`entries`: one row per vulnerability any sourcer has recorded.

| Column | Meaning |
|---|---|
| `entry_id` | integer key |
| `sourcer` | `osv` for this sourcer |
| `primary_id` | preferred advisory id (GHSA first); NULL when a sourcer has no advisory |
| `ids` | every advisory id and alias (GHSA, CVE, PYSEC, GO, RUSTSEC, BIT, ...) |
| `cve` | CVE ids |
| `ecosystems`, `packages` | OSV ecosystems; `ecosystem:name` list |
| `repo` | `owner/name`, lower case |
| `fix_commits`, `n_fix_commits` | every fix SHA referenced |
| `fix_commit`, `fix_commit_date` | the commit the metrics describe (full SHA once known) and its date |
| `parent_commit` | its first parent, the vulnerable state (NULL until `parents` has run) |
| `cwe_ids`, `published`, `modified`, `severity`, `cvss`, `summary` | from the advisory |
| `adv_signals` | JSON of text signals: `fix_bypass`, `bypass_word`, `multi_site_text`, `cause_layer_text`, `defence_text`, `semantic_kw`, `entry_guess`, `services_guess`, `platform_only`, `prs`, `commits_in_other_repos` |
| `src_files`, `src_added`, `src_removed`, `src_hunks` | non-test source change of `fix_commit` |
| `test_files`, `tests_in_fix`, `other_files`, `language`, `file_breakdown` | rest of the diff metrics |
| `repo_stars`, `repo_size_kb`, `repo_flags` | from `repo-meta`, NULL when not looked up |
| `c_*` (18 columns), `lang_tier` | computed difficulty signals, see above |
| `j_*` (8 columns) | reader's JUDGEMENT, NULL when unread |
| `status` | `deferred`, `pending`, `rejected`, `candidate`, `shortlisted` |
| `shortlist_role` | `main` or `control` when shortlisted |
| `reject_reason` | see stages 1, 2 and 4 |
| `score`, `score_read`, `score_detail` | stage 5 |
| `notes` | caveats (merge commit, unfetched commits, commits in other repos) |
| `scanned_at`, `updated_at` | UTC timestamps |

`entry_ids (id PRIMARY KEY, entry_id)`: every advisory id and alias. Dedupe key 1.

`commits (repo, sha PRIMARY KEY, entry_id, source, full_sha, parent_sha, fetch_status,
is_merge, n_patches, subject, commit_date, src_files, src_added, src_removed, src_hunks,
test_files, other_files, language, file_breakdown, src_paths, shape, fetched_at)`: every
commit looked at, with its own metrics. Dedupe key 2.

`runs (run_id, sourcer, stage, args, started_at, finished_at, counts)`: one row per stage
execution, with the funnel counts of that execution (including how many malware records
were skipped, which are not stored as entries).

New columns are added to an existing database automatically when it is opened
(`ADDED_COLUMNS` in `index_db.py`).

### Lookups for other sourcers

```python
import index_db
idx = index_db.Index("index/candidates.sqlite")
idx.seen_id("CVE-2026-12345")              # entry_id or None; any advisory id or alias
idx.seen_commit("Owner/Repo", "abc1234")   # entry_id or None; full or abbreviated SHA
idx.seen_repo("owner/repo")                # list of entry_ids
eid = idx.add_entry("seeded", ids=[], fields={"repo": "owner/repo", "status": "pending"},
                    commits=["<sha>"])
idx.update_entry(eid, status="rejected", reject_reason="...")
idx.commit()
```

## Limits to know about

- Advisories that reference only a pull request or only a release tag are rejected at stage
  1 as `no_fix_commit*`; they are not resolved to commits.
- Malware records are counted, not stored.
- Entry point and services in the shortlist are guesses; the `j_*` columns, "tempting wrong
  fix" and "why hard" are one reader's judgement.
- Nothing is built, run or exploited by this sourcer.
