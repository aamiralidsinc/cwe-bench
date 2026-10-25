# New advisory sources for the sourcer (2026-10-24)

**Status:** in progress; source register in `../sources_and_usage.md`. Results so far are in "Results, 2026-10-24" at the end.

**Today:**
- **What we read:** 7 of the 46 ecosystem files that OSV.dev publishes (45 ecosystems, plus one empty
  entry): Go, Maven, Packagist, PyPI, RubyGems, crates.io and npm.
- **How:** `sourcer/osv_sourcer.py:49` downloads
  `https://osv-vulnerabilities.storage.googleapis.com/<eco>/all.zip`.

**Columns of the count table below** (counted on the 2026-10-24 dumps by
`/private/tmp/claude-501/-Users-dev-terminal-bench/b70882b1-f2eb-4f1e-a8fe-bd7ed8aef484/scratchpad/osvcount.py`):
- **Fix commit:** the record gives a fixed commit in a GIT range, or a GitHub commit link.
- **No GHSA link:** the record carries no GHSA id or alias. Those are the records the GitHub data we
  already read could not contain.

## Confirmed (we both agree)

| # | Source | Why |
|---|---|---|
| C1 | **GitHub unreviewed advisories** (`github/advisory-database`, `advisories/unreviewed/`) | CVE records GitHub never mapped to a package. OSV.dev does not carry them, so they are absent from our dumps. Less reviewed, so less looked at. |
| C2 | **OSV `GIT` ecosystem** (200 MB) | CVE records mapped to git repositories with commit ranges. It opens C/C++ and repositories without a package manager, which we have never tried. |
| C3 | **OSV `NuGet`** (.NET) | 1,965 records, of which 782 MAL. 533 have a fix commit, across 132 repositories. All 1,183 non-MAL records are linked to GHSA, but our dumps never included NuGet. A new language for us. |
| C4 | **WordPress plugins** (Wordfence Intelligence, WPScan, Patchstack; not in OSV) | A large PHP long tail of small, real applications. |

## Concerns on the confirmed list

- **C1 and C2 overlap.** Both come mostly from NVD CVE records. Deduplicate them by CVE id before
  counting either.
- **C1 quality.** Unreviewed records have no package mapping, and many have no fix commit. The fix
  commit has to be mined from the reference URLs. Expect a low yield per record.
- **C2 build cost.**
  - C/C++ tasks need a build recipe for each project (cmake, autotools, system libraries).
  - Our builder has only built managed-language tasks so far.
  - Run a pilot of about 5 tasks before scaling up.
- **C4 terms and data shape.**
  - **Terms:** each provider has its own terms of use, and the free WPScan API has a small daily
    quota. Check each provider's terms, and record the licence with each task (per the licence
    policy), before any bulk pull.
  - **No fix commit:** plugins live in the WordPress SVN. The fix is the difference between the
    vulnerable and the fixed version, so the sourcer needs an SVN or zip-diff step.
  - **Heavier tests:** they need PHP, a database and WordPress itself.

## GitLab Advisory Database: how to tell unique from duplicate

**Record format:** each GitLab record (YAML, in `gemnasium-db` or the public `advisories-community`
mirror) has:
- an `identifiers` list: CVE, GHSA, or GitLab's own `GMS-…` id;
- `package_slug`;
- the affected and fixed versions;
- `urls`.

**A record counts as unique only if it passes all three steps, in this order:**
1. **The ids.** Drop the record if any CVE or GHSA id in `identifiers` is already in our index, or
   in C1 or C2.
2. **The fix.** For the rest, drop the record if its fix commit (from `urls`), or its
   `(package, fixed version)`, matches an index entry. This catches the same bug filed under a
   different id.
3. **What is left is unique.** Records that carry only a `GMS-` id and pass step 2 are the real
   additions.

**Do this before deciding:** count the unique records first. If they are a small fraction (I expect
most GitLab records to carry a CVE or GHSA id), GitLab adds little.

**Concern:** check the database's licence and terms before mining it.

## Small ecosystems: counted

| Ecosystem | Records | MAL | Fix commit | No GHSA link + fix commit | Repos | Verdict |
|---|---|---|---|---|---|---|
| Hex (Erlang/Elixir) | 386 | 0 | 366 | 11 | 124 | **include**: good yield, a new language, server code (Phoenix, Plug) |
| GitHub Actions | 56 | 0 | 40 | 0 | 35 | **include**: workflow-injection bugs are testable; small |
| SwiftURL | 64 | 0 | 43 | 0 | 26 | **include, with a filter**: keep only packages that build on Linux |
| Pub (Dart) | 14 | 0 | 12 | 0 | 8 | include if cheap; skip Flutter apps |
| opam (OCaml) | 35 | 0 | 35 | 32 | 16 | include; small, mostly not on GitHub's list |
| Hackage (Haskell) | 33 | 0 | 16 | 14 | 13 | include; small, heavy builds |
| Julia | 1,717 | 0 | 423 | 261 | 86 | **concern**: many may describe wrapped C libraries rather than Julia code; check a sample |
| OSS-Fuzz (C/C++) | 4,270 | 0 | 3,802 | 3,802 | 357 | **concern**: ARVO and CyberGym are built from it (recall risk); fuzz reproducers exist; C/C++ build cost as in C2 |
| CRAN (R) | 14 | 0 | 0 | 0 | 0 | **drop**: no fix commits |
| VSCode | 21 | 21 | 0 | 0 | 0 | **drop**: all malicious-package reports |
| GHC | 3 | 0 | 0 | 0 | 0 | **drop** |

**Not counted, and why:**

| Ecosystem | Reason |
|---|---|
| Linux (kernel, 56 MB) | real bugs, but tests are very hard to build; a separate decision |
| Bitnami | re-packages advisories we already have |
| Distributions (Debian, Ubuntu, Red Hat, SUSE, Alpine, AlmaLinux, Rocky, openSUSE, openEuler, Mageia, Azure Linux, Chainguard, Wolfi, MinimOS, BellSoft, Alpaquita, CleanStart, Echo, TuxCare, Root, UVI) | packaged versions of upstream bugs, so mostly duplicates; GSD is a retired id scheme |

## Next step

Download C1, C2 and C3 plus the "include" rows, and run them through the index's filters:
- has a fix commit;
- repository size;
- not DoS-only;
- not already screened or built;
- deduplicated by id, then by fix commit.

Then compare the candidate counts per source before building anything.

## Results, 2026-10-24

**Where it lives:**
- **Code:** `cwe-bench/sources2/`.
- **Data:** `~/.tb-graders/cwe/sources2-data/`.
- **Index:** `sources2/index/candidates.sqlite`, a copy of the main index. Entries with an
  `entry_id` above 37416 are new.
- **Method:** the unchanged sourcer (`sourcer/osv_sourcer.py --data ... --index ...`) parses the new
  dumps into the copy. Its parse stage skips any advisory whose id or alias is already indexed, so
  duplicates by id drop out. The main index is not touched.

**Preparation (new scripts, sourcer unchanged):**
- **`make_unreviewed_zip.py`:** 357,496 unreviewed advisories; 11,377 have a GitHub fix commit
  (10,314 also have a CWE). Only those 11,377 are kept, as agreed.
- **`enrich_git_cwe.py`:** only 43,795 of the 118,021 GIT records had a CWE, so CWE ids were added
  from the NVD feeds for 41,509 more. 32,717 still have none (OSS-Fuzz, GSD and freshness records,
  which have no CVE).

**Parse result:** 91,448 new entries. Pending means: inside the window (published from
2026-06-01), with a CWE, a GitHub repo and a fix commit.

| Source | Pending | Deferred (before 2026-06-01) | Rejected |
|---|---|---|---|
| C1 unreviewed | 2,585 | 7,809 | 790 |
| C2 GIT | 7,114 | 12,726 | 59,318 |
| C3 NuGet | 130 | 649 | 327 |

- **Repositories:** the 9,829 pending entries span 2,375 repos.
- **Duplicates by fix commit:** only 40 pending entries share a fix commit with an older entry.
- **C1 is almost entirely inside C2:** 2,563 of the 2,585 pending C1 entries merged with a GIT entry
  (same CVE). C1 adds about 22 entries of its own.

**Diffs stage:**
- Started 2026-10-24 at about 19:07 ET, `--delay 1.0 --max-minutes 330`, about 3 s per patch.
- The full queue is about 16,400 fetches (about 14 h). The cap covers the top-priority ~40%; it can be
  resumed with the same command.
- Then `classify`, `repo-meta`, `parents` and `propose`, all against the sources2 index.
- Log: `~/.tb-graders/cwe/sources2-data/diffs.log`.

**C4 WordPress:** terms checked (`reports/C4-WORDPRESS-TERMS.md`).

| Provider | Verdict | Why |
|---|---|---|
| Wordfence Intelligence | **use** | permissive licence; commercial use allowed; one bulk JSON feed; attribution kept per record |
| WPScan | **drop** | terms forbid storing the data and third-party use |
| Patchstack | **drop** | terms forbid storing the data and third-party use |

- **Plugin code:** GPL; version zips from `downloads.wordpress.org/plugin/<slug>.<ver>.zip`, with no
  account; SVN asks for a 3 s crawl delay.
- **Downloaded 2026-10-24:** 42,842 records, via `sources2/wordfence_fetch.py` (key read from
  `WORDFENCE_API_KEY` in `/Users/dev/terminal-bench/.env`).
- **Converted:** `sources2/wordfence_candidates.py` gives 5,026 pending records over 1,964 plugins
  (865 duplicate CVEs and 49 DoS-only removed). Output: `sources2/out/wordfence_candidates.tsv`, with
  the per-record attribution in `wordfence_attribution.jsonl`.
- **Still to build:** the fix-diff step (last-affected vs first-patched zip).

**Item 5, GitLab** (`sources2/gitlab_unique.py`, run on the MIT-licensed `advisories-community`
mirror; the other copy, `gemnasium-db`, has terms that forbid storing the data):

| | Count |
|---|---|
| Records | 54,063 |
| Duplicate by id | 50,911 (94%) |
| Duplicate by fix commit | 59 |
| Unique | 3,093 |
| Unique with a GitHub fix commit | 102 |
| Unique, with a fix commit, in the window | **7** |

- **Not done:** the planned (package, fixed version) match. The index stores no fixed versions.
- **Verdict:** GitLab adds almost nothing. The 102 are listed in `sources2/out/gitlab_unique.tsv`.

**Item 6, Julia:** **drop.**
- 1,688 of the 1,717 records (98%) are `_jll` binary wrappers of C libraries. Each one points at an
  upstream advisory, which C2 GIT already covers.
- Only 29 records are native Julia, and none has a fix commit in a GIT range.

**Item 7, OSS-Fuzz:** **park, with the C/C++ work.**
- **What it is:** 4,270 records over 359 projects; 3,279 GIT ranges are on GitHub.
- **Bug types:** all memory-safety crashes found by fuzzing: heap-buffer-overflow (1,650),
  uninitialised values (466), use-after-free (338), ...
- **Window:** only 100 records were published from 2026-06-01 (305 in 2026).
- **Recall risk:** ARVO and CyberGym were built from the older records, so the recency window keeps
  us clear of them.
- **No CWE:** the sourcer would reject every record. Mapping the crash type to a CWE (for example
  heap overflow to CWE-122) would be needed.
- **Task shape:** an ASan build plus the fuzz reproducer. Whether the reproducer test cases are
  public is UNCONFIRMED.
