# Stage 1 - Mining

Stage 1 finds recently fixed PyPI and npm vulnerabilities whose fix is a GitHub commit we can extract cleanly. For each one it resolves the pre-patch commit (the single parent of the fix, or the parent of the first commit of a fix series) and merges the result into a cumulative candidate file that stage 2 screens. It reads public advisory feeds and the GitHub REST API. It does not clone repositories. Source: `src/stage1_mining/osv_miner.py` (module docstring and `mine`).

## Inputs and outputs

| What | Path / format |
|---|---|
| OSV bulk export (input) | `https://osv-vulnerabilities.storage.googleapis.com/<eco>/all.zip`, cached as `data/.cache/osv/<eco>.zip` (`download_ecosystem_zip`) |
| GitHub Advisory Database (input) | `GET https://api.github.com/advisories` (`ghsa_candidates`) |
| GitHub commit / compare / repo API (input) | `GET /repos/{owner}/{repo}/commits/{sha}`, `/compare/{a}...{b}`, `/repos/{owner}/{repo}` (`GitHubResolver`) |
| Candidates (output, cumulative) | `data/01_mined/osv_candidates.json`: `{generated_at, ecosystems, count, vulnerabilities: [...]}` (`merge_output`) |
| Dedupe state | SQLite `data/pipeline_state.sqlite3`, table `items`, stage `stage1_mining`, key `owner/repo@sha` (lower-case owner/repo) |

## How it works

1. `main` loads `Config`, parses args, and opens `StateManager` (unless `--ignore-state`).
2. For the `osv` and `huntr` feeds, `candidates_for_ecosystem` downloads each ecosystem export (reused if the cached zip is under 24 h old), skips `withdrawn` records, extracts GitHub fix refs (`extract_fix_refs`), applies `keep_fixes`, and sorts the records newest `published` first.
3. For the `ghsa` feed, `ghsa_candidates` pages through reviewed advisories, skips withdrawn ones, converts each to an OSV-shaped dict (`ghsa_to_osv`), and runs the same extraction.
4. `mine` builds the feeds in this order: `huntr`, `ghsa`, `osv`. It tags every fix key with each feed that produced it, then walks the feeds round-robin (`interleave`).
5. For each item, until `--limit` new records are collected:
   - skip it if the advisory `published` date is before `PUBLISHED_AFTER` (no state write, no GitHub call);
   - skip it if this fix key was already seen in this run;
   - skip it if `state.should_process("stage1_mining", key, 2)` is false;
   - resolve the pre-patch commit: `resolve_series` for a fix series, `parent_of` for a single fix;
   - reject it if the fix commit date is before `PUBLISHED_AFTER`;
   - otherwise append a `MinedVuln`.
6. Every `--batch-size` records (and once at the end), the `checkpoint` callback in `main` runs `merge_output`, then marks those fix keys `DONE` in state. State is only written after the output file is on disk.
7. `main` returns 0 even when nothing new was mined, so later stages still run.

## Rules and techniques

- **Feeds** (`SOURCES = ("osv", "ghsa", "huntr")`):
  - `osv`: every non-withdrawn record in the ecosystem export that has a GitHub fix commit.
  - `ghsa`: query parameters are `type=reviewed`, `ecosystem=pip|npm`, `per_page=100`, `sort=published`, `direction=desc`, plus optional `severity` and `cwes`. The query fetches `--ghsa-pages` pages (default 3) per ecosystem.
  - `huntr`: not a separate API. It is the subset of **OSV-export** records that have a reference matching `HUNTR_RE` (`huntr.com` or `huntr.dev` `/bounties/<hex id, 8+ chars>`). That URL is stored as `report_url`.
- **Interleaving**: `interleave` takes one item from each feed in turn (huntr, ghsa, osv) and drops a feed when it runs out. Inside a feed, items are grouped by ecosystem in the order of `--ecosystems`, newest first within each ecosystem. Ecosystems are not interleaved with each other.
- **Fix-commit extraction** (`extract_fix_refs`):
  - references of type `FIX` or `WEB` whose URL matches `GH_COMMIT_RE`: `github.com/<owner>/<repo>/commit/<40-hex sha>`, optionally followed by `.patch` or `.diff`;
  - `affected[].ranges[]` entries of type `GIT` whose `repo` matches `GH_REPO_RE` and whose `events[].fixed` is a full 40-hex SHA;
  - results are de-duplicated by `owner/repo@sha` (lower case).
- **Several fix commits** (`keep_fixes`):
  - exactly one fix: it is used;
  - several fixes in one repository: kept as a series (`rec["_fix_series"]`);
  - fixes spread over several repositories: skipped, unless `--allow-multi-commit` is set, in which case the first is used.
- **Series and backport resolution** (`GitHubResolver.resolve_series`):
  - every commit must have exactly one parent; otherwise the record is skipped;
  - commits are sorted by commit date, then `compare parent(first)...last` is called;
  - if the status is `ahead` and the commits in range are exactly the fix set, it is a consecutive series: `fixed_commit` = last, `pre_patch_commit` = parent(first), `fix_commits` = all SHAs in date order, and the date used for the cutoff is the earliest one;
  - otherwise it is treated as backports: the resolver walks the fixes newest first and picks the first where `compare <default_branch>...<sha>` returns `behind` or `identical` (the commit is on the default branch). That commit becomes a single-commit fix;
  - if neither applies, the key is marked `REJECTED` ("fix commits are neither one consecutive series nor backports of one default-branch fix");
  - if the result is a different commit than the item's key, that commit is checked again against this run's seen set and the state.
- **Parent resolution** (`_fetch_parent`):
  - the result must have exactly one parent; merge and root commits are a permanent failure;
  - HTTP 404, 422 or 451: permanent failure;
  - 403 or 429 with rate-limit signs: sleep until reset (`_sleep_until_reset`: wait + 2 s, capped at 3700 s);
  - anything else: up to 4 attempts with `2**attempt` s backoff;
  - an unresolved parent is marked `REJECTED` if permanent, `FAILED` otherwise. `FAILED` is retried while attempts < `MAX_RESOLVE_ATTEMPTS = 2`.
- **Commit date**: the earlier of the author and committer dates (`YYYY-MM-DD`), because a cherry-picked or rebased backport gets a new committer date only.
- **Date cutoff** (`PUBLISHED_AFTER`, compared as `YYYY-MM-DD` strings):
  - an advisory published before the cutoff, or with no `published` date, is skipped and does not use a `--limit` slot;
  - a fix committed before the cutoff is marked `REJECTED` in state.
- **Ecosystems**: `SUPPORTED_ECOSYSTEMS = ("PyPI", "npm")`. GHSA names are mapped as `pip` -> `PyPI`, `npm` -> `npm`.
- **Dedupe**:
  - within a run, by fix key (several advisories or feeds can share one fix);
  - across runs, by state key: terminal statuses are never retried (`StateManager.should_process`);
  - the output file is de-duplicated by `osv_id`, and a new record replaces an old one (`merge_output`).
- **Stored per candidate** (`MinedVuln`):

| Field | Content |
|---|---|
| `osv_id` | the advisory id |
| `cve_id` | the first id or alias starting with `CVE-` |
| `ecosystem` | `PyPI` or `npm` |
| `package` | the first affected package in the ecosystem |
| `repo_url` | `https://github.com/<owner>/<repo>` |
| `pre_patch_commit`, `fixed_commit` | the resolved commit pair |
| `summary` | the advisory `summary`, or the first paragraph of `details` (500 chars max) |
| `published`, `aliases` | copied from the advisory |
| `cwe_ids` | `database_specific.cwe_ids` |
| `severity` | `database_specific.severity` |
| `fix_commit_url` | the commit URL |
| `source_refs` | the URLs and ranges the fix came from |
| `sources` | the feed tags |
| `report_url` | the huntr URL, if any |
| `description` | the first 2000 chars of `details` |
| `fix_commits` | the commits in the oracle diff |

## Configuration

| Key / flag | Default | Effect |
|---|---|---|
| `GITHUB_TOKEN` (env) | unset | Bearer auth. Without it, a warning says GitHub allows 60 calls/hour. |
| `PUBLISHED_AFTER` (env) | `''` (no filter) | Date cutoff described above (`Config.published_after`). Project setting: `2026-08-01` (`.env.example`). |
| `CWE_DATA_DIR` (env) / `--data-dir` | `./data` | Data root (`Config.load`). |
| `--limit` | 50 | Number of NEW records per run. Must be >= 1. |
| `--ecosystems` | `PyPI npm` | Ecosystems to mine. |
| `--sources` | `osv ghsa huntr` | Feeds to mine. |
| `--ignore-state` | off | Do not read or write the dedupe state. |
| `--ghsa-pages` / `--ghsa-severity` / `--ghsa-cwes` | 3 / none / none | GHSA query options. |
| `--github-rps` | 2.0 with token, 0.5 without | Request rate (`RateLimiter`). |
| `--batch-size` | 10 | Checkpoint interval. |
| `--allow-multi-commit` | off | Use the first fix when fixes span several repos. |
| `--output` / `--cache-dir` | `data/01_mined/osv_candidates.json` / `data/.cache/osv` | Paths. |

`run_pipeline.py --stage 1` passes only `--limit`, `--ecosystems`, `--sources` and `--ignore-state` (`src/stage1_mining/__init__.py: run`). For the other flags, run `python -m src.stage1_mining.osv_miner` directly. `--reset-state` deletes all `stage1_mining` rows before the run (`run_pipeline.main`). `--batch N` raises `--limit` to `max(limit, 10*N, 30)`.

HTTP sessions (`make_session`) retry 5 times with a backoff factor of 1.5 on 500, 502, 503 and 504, and honour `Retry-After`.

## Code map

| File | Function | Role |
|---|---|---|
| `src/stage1_mining/osv_miner.py` | `download_ecosystem_zip` | Fetch and cache the OSV export (24 h). |
| | `iter_osv_records` | Read the JSON records from the zip. |
| | `extract_fix_refs` | Collect GitHub fix commits from references and GIT ranges. |
| | `keep_fixes` | Choose single fix / series / skip. |
| | `GitHubResolver.parent_of`, `_fetch_parent` | Find the single parent and record the commit date. |
| | `GitHubResolver.resolve_series` | Handle a consecutive series or pick the default-branch backport. |
| | `ghsa_candidates`, `ghsa_to_osv` | GHSA feed and its conversion to OSV shape. |
| | `huntr_url` | Detect a huntr bounty reference. |
| | `interleave` | Round-robin across feeds. |
| | `mine` | Main loop: filters, dedupe, resolution, checkpoints. |
| | `merge_output` | Atomic, cumulative write, de-duplicated by `osv_id`. |
| | `parse_args`, `main` | CLI and state lifecycle. |
| `src/stage1_mining/__init__.py` | `run` | Adapter called by `run_pipeline.py`. |
| `src/common/state_manager.py` | `should_process`, `mark`, `reset` | Cross-run dedupe. |
| `src/common/config.py` | `Config.load` | Env settings and paths. |

## Known limitations

- Ecosystems are not interleaved inside a feed, although the `interleave` docstring says "across ecosystems". With a small `--limit`, the `osv` feed returns the first ecosystem's records first.
- `huntr` covers only OSV-export records. The module docstring says "OSV/GHSA records", but `mine` checks `huntr_url` only on `osv_by_eco`.
- Only GitHub commit URLs and full 40-char SHAs are recognised. Pull-request links, short SHAs and other hosts produce no candidate.
- If a parent lookup inside `resolve_series` fails because of a temporary error, the key is still marked `REJECTED`, so it is never retried.
- OSV `published` can be a re-publication date. For example, a stored record for CVE-2021-4118 has `published` 2026-09-10. Only the fix-commit date check catches these.
- In `ghsa_candidates`, a rate-limit retry uses up one of the `--ghsa-pages` iterations.
- Records mined by older code versions lack some fields: at the time of writing, 173 of 610 records have `fix_commits`.
