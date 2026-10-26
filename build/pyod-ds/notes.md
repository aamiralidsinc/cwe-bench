# pyod-ds — build notes

- slug: `pyod-ds`
- candidate: screener-v2 entry 2423 — GHSA-997V-R4V7-9F3G / CVE-2026-15529 / PYSEC-2026-3909
  (yzhao062/pyod, CWE-502, validation ordered after unpickling)
- track: injected, pattern B
- started (UTC): 2026-10-24T05:24:16Z
- finished (UTC): 2026-10-24T08:46:18Z (session paused ~1 h while the host Docker daemon was repaired)

## Verified before designing

- `pyod/utils/persistence.py:215` `load()` calls `joblib.load(path)` first; envelope/version
  validation only happens afterwards in `_handle_loaded_object`. Confirmed behaviourally: an
  envelope-shaped artifact whose `model` entry carries a `__reduce__` writes a marker file and
  `load()` returns normally.
- Published fix `16e6e3a` (merge; source commit `bc31755`) adds a keyword-only
  `trusted: bool = False` to `load()` and raises before `joblib.load`. It touches only
  `pyod/utils/persistence.py`; `compat_load`, `_load_with_unpickler` (incl. the pre-0.10
  `load_compatibility` branch), `BaseDeepLearningDetector.load` and the MCP tool data loader stay
  open at that commit. The fix commit adds its regression test (`TestLoadTrustBoundary`); the
  pinned commit does not contain it, and there is no other regression test between pinned and fix.
- Real routes confirmed on the pinned code (marker written, no exception):
  - `compat_load()` on an envelope artifact and on a pre-0.10 z-file container (the latter reaches
    joblib's `load_compatibility`, which does not use the reader's own unpickler class —
    `pyod/utils/persistence.py:481-484`);
  - `load()` with a `Path`, an open file object, a compressed artifact, a raw pickle and
    `strict=True`;
  - `AutoEncoder.load()` (`pyod/models/base_dl.py:347`, raw `pickle.load`, no gate ever).
- A plain `pickle.dump` file is NOT the legacy shape: joblib detects it as `not-compressed` and
  uses the modern unpickler. The legacy branch needs the `ZF` container, so the security test
  builds one (tag + fixed-width hex length + zlib payload).
- `pyod/test/test_persistence.py` (31 tests) passes on the pinned commit in a 3.12 venv.
- `AutoEncoder()` + `save()`/`load()` round trip is fast offline (<1 s after import).

## Security property (stated once, general)

No file may run code, or create/change anything on disk, merely because the library reads it; the
read must fail with an exception before any of the content is deserialized unless the caller has
vouched for the source. Holds for every public way the library reads a saved object, every shape of
file accepted, and whether or not stricter checking is requested.

Contract stated once: the reading call takes `trusted` (default false); `trusted=True` keeps
today's behaviour exactly.

## Levers

1. **L_order (how-type: ordering — validation must precede deserialization).** The trust decision
   must be taken before the artifact is unpickled, not added to the post-load envelope/schema
   validation. Why a solver dismisses it: the module already has a validation stage that looks like
   the right home for a trust check, and putting the check there still makes the call raise — but
   only after the reducer ran.
   Site: `pyod/utils/persistence.py:215`. Security tests: the five marker cases in
   `test_load_untrusted.py`. Wrong fix: `sf-after-load.patch`.
2. **L_dl (how-type: route where the protection never existed; far site).** The deep-learning
   detectors carry their own `save`/`load` pair in `pyod/models/base_dl.py` that uses raw
   `pickle.load` and never had any gate. Why a solver dismisses it: another package, a model-class
   method rather than the persistence wrapper the report names, and plain pickle rather than
   joblib. Site: `pyod/models/base_dl.py:332-348`. Wrong fix: `sf-no-dl.patch`.
3. **L_legacy (how-type: shape a plausible check mishandles).** `compat_load()` feeds a pre-0.10
   container to joblib's `load_compatibility`, which bypasses the custom unpickler class; a fix
   that restricts the unpickler class instead of gating the call leaves this branch open. Why a
   solver dismisses it: the legacy format is deprecated, so it reads as irrelevant to a modern
   artifact. Site: `pyod/utils/persistence.py:387-449, 481-484`. Wrong fix:
   `sf-no-legacy-branch.patch`.
4. **L_repair (how-type: coupled must-keep-working).** The dtype-drift repair and envelope-less
   artifacts must still load when the caller vouches. Why a solver skips it (over-hardening):
   refusing everything that is not a fresh envelope looks safer.
   Site: `pyod/utils/persistence.py:276-318`. Wrong fix: `ff-overbroad.patch`.
5. **L_inspect (where-type, injected).** A "metadata-only" inspector that returns the stored
   envelope without the model — it unpickles the whole artifact to get there. Why a solver
   dismisses it: it is a read-only metadata helper that drops the model.
   Site: `pyod/utils/persistence.py` (injected `inspect_artifact`). Wrong fix:
   `sf-no-inspector.patch`.
6. **L_tool (where-type, injected).** The agent tool server's data-file loader dispatches on
   extension; the injected `.pkl`/`.joblib` branch unpickles an agent-supplied path. Why a solver
   dismisses it: it is the tool layer's data loader, not a model-loading API.
   Site: `pyod/mcp_server.py` `_load_data` (injected branch). Wrong fix: `sf-no-tool.patch`.

Different dismissal reasons: 1 (right-looking validation stage), 2 (different package/API),
3 (deprecated format), 4 (over-hardening is safer), 5 (read-only metadata), 6 (tool data layer).

## Sibling candidate list (every site/route found) and why each pick won

| # | candidate | kind | picked? | why / why not |
|---|-----------|------|---------|----------------|
| 1 | `BaseDeepLearningDetector.load` (`base_dl.py:347`) | real upstream | **yes (L_dl)** | far package, never had a gate, raw pickle; highest dismissal value |
| 2 | `compat_load` public API (`persistence.py:387`) | real upstream | **yes (with 3)** | separate public entry point the upstream fix left open |
| 3 | `_load_with_unpickler` pre-0.10 branch (`persistence.py:481-484`) | real upstream | **yes (L_legacy)** | a shape a plausible restricted-unpickler fix mishandles |
| 4 | `load()` fall-through to `compat_load` (`persistence.py:301-312`) | real upstream | no | same sink and same call chain as 2; a second test adds nothing |
| 5 | `load()` with file-like / `Path` / compressed input | real upstream | yes, as *shapes under L_order* | same entry point, tested as input forms, not as separate levers |
| 6 | `mcp_server._load_data` extension dispatch | injected | **yes (L_tool)** | different product surface (agent tool layer), plausible extension branch |
| 7 | `persistence.inspect_artifact` metadata reader | injected | **yes (L_inspect)** | docs already promise such an API; "read-only" is a strong dismissal |
| 8 | `persistence.load_from_bytes` bytes helper | injected | no | same module as 7, same concept, where-type duplicate |
| 9 | `BaseDeepLearningDetector.load_from_bytes` | injected | no | second sibling in the same file as 1; falls with 1 |
| 10 | a model-artifact CLI subcommand | injected | no | no existing CLI surface reads artifacts; would require inventing a feature |
| 11 | `ADEngine` artifact/registry restore | injected | no | no persistence surface exists in the engine; inventing one is not "code a maintainer could have left" |
| 12 | `pyod/utils/encoders` local-path model loading | real upstream | no | not a pickle sink (sentence-transformers local path), different mechanism |

Picked siblings: 1, 2+3, 6, 7 — the most complex/distant candidates, each with a distinct reason
to skip.

## Test plan and what was verified locally (venv, same pins as the image)

- Security, 10 tests: `load` (envelope, compressed, raw pickle, open file, strict),
  `compat_load` (envelope, pre-0.10 container), `AutoEncoder.load`, `inspect_artifact`,
  tool data path. On the pinned+injection tree all 10 fail (the marker file appears).
- Functional, 14 hidden tests + the project's own 30 persistence tests: all pass on the pinned
  tree and after the reference fix (a `trusted=True` call falls back to the plain call on a
  `TypeError`, so the same scenario runs before and after the API change).
- Reference fix: 24 hidden + 30 project tests pass.
- Patches (each verified by applying it to the pinned+injection tree and running the suites):
  `sf-after-load` 5 security fail; `sf-no-legacy-branch` 1; `sf-no-dl` 1; `sf-no-inspector` 1;
  `sf-no-tool` 1; `sf-load-only` (published fix only, kept as evidence) 5; `ff-overbroad` 1
  functional fail; `pass-alt` and `pass-hardening` 24 + 30 pass. All patches apply with
  `patch -p1` to the pinned+injection tree.
- The project's own test file is shipped with two adaptations: a wrapper that vouches for the
  source (dropping the keyword when the revision does not accept it), and one test dropped because
  it pins the internal call shape of the repair fall-through (it monkey-patches the module-level
  repair entry point and asserts the exact call), which any correct trust gate perturbs.

## Not verified / guesses

- `present_in_latest` was checked by a read-only clone of today's upstream (f0d0967):
  the deep-learning reader is still ungated there (`yes`); the second public reader now takes a
  trust argument upstream, so it is `no` for the compat route.
- The screener's `repo_mb`, `O11_fix_minutes`, and its "fix.diff has no hunks" note are moot once
  the real fix commit was read (it has hunks).
- The gate stages run here (`static`, `nop`, `oracle`, `patches`) are reported with their results
  in the build report; the pipeline re-gates after the builder exits.

## Gate results (this build, run with builder/gate.py)

| stage | result |
|-------|--------|
| static | PASSED |
| nop | PASSED — 10/10 security tests fail on the pinned code, 44/44 functional tests pass (14 hidden + 30 project) |
| oracle | PASSED — 3 runs, each reward 1.0, 10/10 security and 44/44 functional, identical results |
| patches | PASSED — sf-after-load 0.5 (5 security failing); sf-no-legacy-branch / sf-no-dl / sf-no-inspector / sf-no-tool 0.9 (1 security failing each, no functional failure); ff-overbroad 0.0 (2 functional failing); pass-hardening 1.0; pass-alt 1.0. The `blind` check was not run (written after the build). |

`checks/sf-load-only.patch` (the published fix applied to the reported call only) is kept in
`checks/` as evidence but is not listed in `patch_checks`; the five per-lever security-fail
patches supersede it.

## Fairness self-check

- Every tested route is reachable by grepping the repository for the two deserialization
  primitives; the instruction's property ("every public way the library reads a saved object")
  covers each one without naming it.
- The refusal contract (`trusted`, default false; `trusted=True` behaves as today) is stated once
  and used by both suites; the functional suite falls back to the plain call when a revision does
  not accept the keyword, so the same scenarios run before and after the API change.
- The coupled values (envelope-less artifacts, the dtype-repair path, the round trip, the tool's
  other data formats) are named in the instruction only as "every file the library reads today".
