# Sources and usage (CWE-bench candidate sources)

Last updated 2026-10-24. This file is the reference for **which sources the pipeline uses, where
each is pulled from and how, and which are held in reserve**. Plan, counts and reasoning:
`reports/NEW-SOURCES.md`. Terms for the WordPress providers: `reports/C4-WORDPRESS-TERMS.md`.

**The rule:**
- **In use:** the pipeline draws candidates ONLY from the in-use source (S0).
- **Reserve:** reserve sources (R1-R5) are pulled and indexed, but not used. Draw on them only when
  S0 runs short of candidates, one source at a time, picked with `sources2/select_source.py`.
- **Parked:** recorded, not pulled. **Dropped:** not used, with the reason.

**Where things live:**
- `sourcer/` holds the in-use sourcer and the main index. It is unchanged by any reserve work.
- `sources2/` holds the reserve sources' scripts, their own index (a copy of the main index plus
  the reserve entries) and their tables.
- **Data:**
  - S0: `~/.tb-graders/cwe/sourcer-data/`.
  - Reserve sources: `~/.tb-graders/cwe/sources2-data/`.
  - All downloads are untrusted data, parsed only as JSON or text.

## In use

| Id | Source | Pulled from | How | Local data | Licence / terms | Index |
|---|---|---|---|---|---|---|
| **S0** | **OSV.dev, 7 ecosystems**: PyPI, npm, Go, crates.io, Maven, RubyGems, Packagist | `https://osv-vulnerabilities.storage.googleapis.com/<eco>/all.zip` | `sourcer/osv_sourcer.py fetch-dumps`, then `parse`, `diffs`, `classify`, `parents`, `repo-meta`, `propose` (see `sourcer/README.md`) | `sourcer-data/dumps/<eco>.zip`, `sourcer-data/patches/` | per upstream source: GitHub GHSA is CC-BY 4.0; also PYSEC, GO, RUSTSEC, DRUPAL, BIT, SNYK records merged by alias | `sourcer/index/candidates.sqlite` (sourcer `osv`, 37,416 entries; 2,511 `candidate`, 20 `shortlisted`); read by the screeners and `sibling2/pick.py` |

**What S0 contains:**
- Most S0 records are GitHub's reviewed advisories (35,726 GHSA ids).
- Only records published from 2026-06-01 are candidates; older ones are `deferred` (the recency
  window).

**Supporting data:** these are not candidate sources.

| Data | Where | Used for |
|---|---|---|
| NVD CVE 2.0 yearly feeds (`https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-<year>.json.gz`) | `~/.tb-graders/cwe/research-raw/item4-severity/nvd-feeds/` (2012-2026, 2026-10-15); 2025 and 2026 refreshed into `sources2-data/nvd/` on 2026-10-24 | the severity research; CWE enrichment for R2 |

The NVD terms ask for the notice "This product uses the NVD API but is not endorsed or certified by
the NVD."

## Allocated to the diversity experiment (from 2026-10-27)

The `diversity_population/` experiment takes its candidates **only** from the slices below, so it never competes with
the main pipeline.

| Id | Slice | Why it is separate |
|---|---|---|
| **D1** | S0 entries with status `deferred`, published 2025-01-01 to 2026-05-31 | the main pipeline's window starts on 2026-06-01, so it never reads them |
| **D2** | R1–R3 entries in the sources2 index (any status), published from 2025-01-01 | the main pipeline reads only S0 |

**Rules:**
- **No shared repos.** D1 and D2 exclude any repo that has a candidate in the main pool, or that any pipeline has
  built.
- **One owner per slice.** If the main pipeline ever widens its window, or starts drawing on R1–R3, first agree which
  side owns D1 and D2.
- **Work on a copy.** The experiment fetches diffs and scores on its own copy of the index. The main index is read
  only.

## Reserve: pulled, indexed, not used until S0 runs short

| Id | Source | Pulled from | How | Local data | Licence / terms | Where it is | Pending (2026-10-24) |
|---|---|---|---|---|---|---|---|
| **R1** | GitHub **unreviewed** advisories, only those with a GitHub fix commit | git sparse clone of `https://github.com/github/advisory-database`, `advisories/unreviewed/` | `sources2/make_unreviewed_zip.py`, then the S0 sourcer with `--ecosystems GHSA-unreviewed` | `sources2-data/raw/advisory-database/`, `dumps/GHSA-unreviewed.zip` (11,377 records) | CC-BY 4.0 | sources2 index, `ecosystems` contains `GHSA-unreviewed` | 2,585, but only **22** are R1-only; the rest share a CVE with R2 |
| **R2** | OSV.dev **GIT** ecosystem (CVE records mapped to git repos; opens C/C++) | `.../GIT/all.zip` | `sources2/enrich_git_cwe.py` (adds NVD CWEs to 41,509 records), then the S0 sourcer with `--ecosystems GIT` | `sources2-data/raw/GIT.orig.zip`, `dumps/GIT.zip` (enriched) | per upstream: OSV, CVE and NVD terms | sources2 index, `ecosystems` contains `GIT` | 9,803 (7,114 GIT-only); many C/C++, which waits for a C/C++ pilot |
| **R3** | OSV.dev **NuGet** (.NET) | `.../NuGet/all.zip` | the S0 sourcer with `--ecosystems NuGet` | `sources2-data/dumps/NuGet.zip` | GHSA, CC-BY 4.0 | sources2 index, `ecosystems` contains `NuGet` | 130 |
| **R4** | **Wordfence Intelligence**: WordPress plugins | `https://www.wordfence.com/api/intelligence/v3/vulnerabilities/production` (free account key, in `/Users/dev/terminal-bench/.env` as `WORDFENCE_API_KEY`) | `sources2/wordfence_fetch.py`, then `sources2/wordfence_candidates.py` | `sources2-data/raw/wordfence/production-<UTC>.json` (42,842 records) | Defiant licence: commercial use and derivative works allowed. **Every copy must keep the record link, Defiant's copyright notice and its licence text** (plus MITRE's where present), kept per record in `sources2/out/wordfence_attribution.jsonl`. Plugin code is GPL and stays GPL. | `sources2/out/wordfence_candidates.tsv` (its own table: no fix commit and no GitHub repo, so the S0 sourcer cannot take it) | 5,026 over 1,964 plugins (865 dropped as duplicate CVEs) |
| **R5** | **GitLab Advisory Database**, community mirror (30 days delayed) | `git clone --depth 1 https://gitlab.com/gitlab-org/advisories-community.git` | `sources2/gitlab_unique.py` (removes duplicates by id, then by fix commit) | `sources2-data/raw/advisories-community/` (54,063 records) | MIT | `sources2/out/gitlab_unique.tsv` | 3,093 not seen elsewhere; 102 have a GitHub fix commit; **7** are in the recency window |

**R1-R3 are not candidates yet:**
- They have passed `parse`.
- `diffs` is running (started 2026-10-24, about 0.5 fetches/s, resumable; log
  `sources2-data/diffs.log`).
- `classify`, `parents`, `repo-meta` and `propose` follow.
- The command is the S0 one, run with
  `--data ~/.tb-graders/cwe/sources2-data --index sources2/index/candidates.sqlite`.

**R4 still needs a fix-diff step:** download the last-affected and first-patched zips from
`downloads.wordpress.org/plugin/<slug>.<version>.zip` (SVN asks for a 3 s crawl delay), then diff
them. Not built yet.

## Parked: recorded, not pulled

| Id | Source | Why parked | What it needs |
|---|---|---|---|
| P1 | OSV.dev **OSS-Fuzz** | C/C++ memory-safety crashes (4,270 records, 359 projects, 100 in the window) | the C/C++ pilot first. The records have no CWE: map the crash type to a CWE. Reproducer access UNCONFIRMED. The window avoids ARVO/CyberGym overlap. |
| P2 | OSV.dev **Hex, GitHub Actions, SwiftURL, Pub, opam, Hackage** | small (366 / 40 / 43 / 12 / 35 / 16 records with a fix commit) | a pull with the S0 sourcer like R3. SwiftURL: only packages that build on Linux. |
| P3 | OSV.dev **Linux** (kernel) | real bugs, but tests are very hard to build | its own decision |

## Dropped

| Source | Reason |
|---|---|
| WPScan | terms forbid permanent storage and commercial use without a paid licence; Enterprise forbids storing data |
| Patchstack | terms forbid derivative works, third-party benefit and disclosure |
| GitLab `gemnasium-db` | terms forbid downloading or storing the content (use R5 instead) |
| OSV.dev **Julia** | 98% `_jll` binary wrappers of C libraries (their upstream advisories are in R2); 29 native records, none with a fix commit |
| OSV.dev **CRAN, VSCode, GHC** | no fix commits (VSCode: all malicious-package reports) |
| OSV.dev distributions (Debian, Ubuntu, Red Hat, SUSE, Alpine, ...) and **Bitnami** | packaged copies of upstream bugs, so duplicates |

## Picking one source

```sh
cd /Users/dev/terminal-bench/cwe-bench
python3 -I sources2/select_source.py GIT --status pending --out /tmp/git.tsv          # all with GIT
python3 -I sources2/select_source.py GHSA-unreviewed --only                            # R1-only entries
python3 -I sources2/select_source.py wordfence                                         # R4 pending
python3 -I sources2/select_source.py gitlab                                            # R5 unique
python3 -I sources2/select_source.py osv-main --status candidate                       # S0
```

**How the selector finds a source's entries:**
- **Index sources:** an entry belongs to a source when its `ecosystems` field names it. Entries
  above id 37416 in the sources2 index are the reserve entries; at or below are S0 copies.
- **Shared advisories:** an advisory found in two sources is one entry naming both. Per-source
  counts therefore overlap; `--only` gives a source's own share.
- **Table sources (R4, R5):** each row carries `source` and its record link.

## Changing this file

**When a reserve source is promoted to use:**
- move its row to "In use";
- write the date and the reason;
- say whether its candidates join the main index or stay in sources2.

**When a source is added:** add a row with all columns filled in, including the licence.
