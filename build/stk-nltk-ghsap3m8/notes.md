# stk-nltk-ghsap3m8 — build notes

Started 2026-10-25T22:54:38Z. Ended 2026-10-25T23:30Z.

## Design

Stacked H3b task on `nltk/nltk`, pinned at `b73aa9bc6afa54c335f08d6911f5b9bbba52cd57`
(the first parent of the commit the A advisory references, `441aecb7d330`). The pinned tree
predates the central path-security branch entirely, so the five published protections the reader
listed are absent as code. The reference fix is the complete path-security implementation as it
stands at B (`155e40343cff`) applied to the pinned tree, plus the two routes that published state
still leaves open (decoded resource names and checksum-before-extract).

Concepts (3): destination confinement `[T1,T2]`; resource-read confinement `[T3,T4,T7]`; install
integrity `[T6]`.

## Levers (one line each)

- **T1 / T2 — download destination confinement** (advisory route, deepseek xhard). Index-supplied
  `subdir`, `id` or an overriding `filename` attribute is joined onto the caller's download
  directory with no containment test (`nltk/downloader.py:265,275,691,707,728`); the stale-file
  removal and subdirectory creation consume the path before any check (`:691-699`). Reason to
  dismiss: the index is the project's own HTTPS metadata, so its destination fields read as
  trusted configuration; the pre-transfer cleanup looks covered by a guard at the write call.
- **T3 — resource-read confinement, decoded form** (uncovered upstream, mimo xhard). Parent
  segments survive pre-decode normalisation and `url2pathname` decodes only at the join, so a
  pre-decode check misses percent-encoded and encoded-absolute names
  (`nltk/data.py:237,242,507,531`). Reason to dismiss: `normalize_resource_name` already runs
  `os.path.normpath`.
- **T4 — coupled legitimate value** (uncovered upstream, mimo). Explicit absolute `file:` addresses
  are documented and doctested (`nltk/data.py:15-16,885-887`) and must keep working; a blanket
  read confinement breaks them. Covered by the general keep-working sentence only.
- **T6 — install-time integrity** (uncovered upstream, deepseek xhard). The archive is unpacked
  before any checksum comparison; the only comparison is a later status query
  (`nltk/downloader.py:705-737,896`). Reason to dismiss: the checksum comes from the same index.
- **T7 — corpus file-id join** (published-fix far site, deepseek). A corpus file id is joined onto
  the corpus root with `os.path.join` and no containment test
  (`nltk/data.py:332-334`, `nltk/corpus/reader/api.py:170,195,231`). Reason to dismiss: file ids
  are corpus-internal identifiers and joining them is the documented way to reach a corpus file.

## Dropped / substituted

- **T5 (fetch-target / SSRF) is not built.** It needs a third distinct protection stated in the
  report; with T6 already occupying the one DESCRIBED hidden trap the listing rule allows
  (max 1 described), stating it would make the report fail the listing check. Testing it offline
  also needs a loopback service that the upstream guard itself blocks. T7 was used instead as the
  third concept. The reader's record still lists T5; `score_at_build` was recomputed for the built
  concepts (0.595).
- The pinned tree predates the A fix's code. The A advisory references the 3.8.2 release commit,
  whose diff is release metadata only; the actual path-security code landed later on the develop
  line. `upstream_first_fix.patch` therefore uses that complete implementation with enforcement
  off (the A-era state the B advisory describes), and `upstream_fix.patch` uses it with enforcement
  on (the B state). Both are diff-against-the-pin and both fail the hidden suite (5 security
  failures), so the recall checks are honest about what upstream shipped.
- T3's encoded form and T6 remain open in the B state and were closed by later upstream work; T7
  is closed by the B join guard. This is why `upstream_fix.patch` fails.

## Verified

- Local (Python 3.12 venv, same dependency versions as the images), suites against: the pin
  (14 security fail / 10 functional pass), the reference (24/24), the B state (5 security fail,
  10 functional pass), the A state (same), and every check patch:
  - `miss_destination`: 6 security fail, functional pass.
  - `miss_read_confinement`: 5 security fail, functional pass.
  - `miss_integrity`: 2 security fail, functional pass.
  - `check_after_side_effects`: security fail, functional pass.
  - `alt_correct_fix`, `hardening`: 24/24.
  - `functional_overbroad`, `refuse_all`: functional fail (the latter passes all 14 security
    tests, proving the positive controls).
- Both images build with the classic builder (`DOCKER_BUILDKIT=0`), including the
  claude-code agent layer.
- The verifier was emulated end to end in the real images: nop reward 0.0 (14 security fail /
  10 functional pass), reference reward 1.0 (24/24). The control task in the same emulation:
  nop 6 security fail / 10 functional pass, reference 16/16.
- A pristine copy of the project's `nltk/test/unit/test_data.py` runs in the functional group.
  The project's downloader unit tests call the live NLTK index and cannot run offline.
- `static` and `check_stack.py` pass for the stacked task; `static` passes for the control.

## Not verified / unknowns

- The target-model bar (both models failing three attempts) is not testable in this session; no
  trials were run (`strict_gate` oracle/patches only).
- The listing check was not run here (it needs a model runner); the report is written to keep
  T3/T7 general and leave only T6 described. If the reviewer treats the read-confinement
  property itself as DESCRIBED, that would be a second described trap and the task would need a
  report rewrite.
- The reader record is at `pipelines/stacking/out/reader-ds/h3-ghsa-p3m8-78j2-g5p3.json`, not the
  `out/reader/` path named in the task prompt (the older reader directory has no record for this
  candidate).
- `score_at_build` 0.595 is computed with `score_stack.py`'s functions/weights over the built
  concepts, not by running the script itself (it rewrites pipeline output files outside the
  allowed edit scope).

## Outside the advisory's protection (not built)

- The index parser is stdlib ElementTree (entity-expansion hardening is a separate upstream change,
  `defusedxml`), and there is no SSRF / fetch-target restriction in this task (T5 dropped above).

## Gate (2026-10-25)

- `stk-nltk-ghsap3m8`: static PASSED; nop PASSED (14 security fail, 10 functional pass);
  oracle PASSED (3 runs, all reward 1.0, identical); patches PASSED (10/10 as declared —
  3 concept misses with functional clean, 2 functional-fail, 2 recall security-fail,
  alternative and hardening at 1.0); `check_stack.py` conforming (3 concepts, H3b).
- `stk-nltk-ghsap3m8-control`: static PASSED; nop PASSED (6 security fail, 10 functional
  pass); oracle PASSED (3 runs, all 1.0); patches PASSED (5/5).
- The two `instruction.md` files are byte-identical (check_stack re-verified after the final
  instruction edit).
