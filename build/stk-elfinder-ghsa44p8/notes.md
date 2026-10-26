# stk-elfinder-ghsa44p8 — build notes

Start (UTC): 2026-10-22T19:17Z. Resumed after the builder re-launch: 2026-10-22T22:16Z.
End (UTC): 2026-10-22T23:55Z.

## Levers

- **T1 (pattern A, advisory route)** — `php/elFinder.class.php:1625-1629,1649`: the archive-download
  step joins a client-supplied temporary-file value onto the server scratch path, registers it for
  removal on shutdown and opens it. Reason to dismiss: it is the reported symptom itself.
- **T3 (pattern B, how-type)** — `php/elFinderVolumeLocalFileSystem.class.php:417` (`_inpath`),
  `:450` (`_stat`), `php/elFinderVolumeDriver.class.php:6100` (`getFullPath`): a client-derived
  identifier that decodes to a path ending in a parent segment survives the lexical in-root test,
  because the normaliser collapses only `/seg/../`. Reason to dismiss: the in-root check is already
  present, commented "Prevents directory traveral", and identifiers are opaque. Coupled value:
  stored links whose target lies outside the browsed folder keep working.
- **T4 (pattern B, protection never existed)** — `php/elFinderVolumeDriver.class.php:3574`
  (`nameAccepted`) and the create/rename/upload call sites,
  `php/elFinderVolumeLocalFileSystem.class.php:290` (`_joinPath`): a name that is not a single path
  component is joined verbatim. Reason to dismiss: every create/rename already calls the name
  policy, so the missing path-component rule reads as a deliberate policy. Coupled values: a name
  containing `..` without a separator, a backslash in a name, and a multi-level folder-upload path.

The reader's T2 (Windows backslash) is excluded: not observable on the POSIX grader, and requiring a
backslash refusal there would over-refuse legitimate names. The reader's T5 (clipboard-upload name
override) is a second route into T4's sink, not an independent concept; the upload security test
covers it.

## Verified

- The pinned commit is the first parent of the earlier fix commit: `git rev-parse 157f471d7e48^` ==
  `82b098ff...` in the clone. A = 157f471d7e48 (separator check), B = e6351557b86c (normalises `/`
  for Windows). A alone and A+B both leave T3 and T4 open.
- All three levers reproduce through the real HTTP entry point on the pinned checkout: the local
  runner scores the untouched tree 0/10 security and 6/6 functional; the reference fix scores
  10/10 + 6/6. Each per-concept miss patch leaves only its own concept failing (3, 3 and 4 tests).
- Local variant matrix (same test runner, php:7.4-cli-bullseye container): hardening and alternative
  fixes 10/6; over-broad 10/3; realpath containment 10/5; crash 6/6; wrong-resource 9/6; mkdir-only
  7/6; command-level 9/6; after-registration 7/6; upstream A alone 3/6; upstream A+B 3/6.
- Control task: pinned 0/4 + 6/6; upstream A+B (its reference) 4/4 + 6/6; its catalogue patches
  behave as declared.
- elFinder has no project test suite at the pinned commit (only `php/chars-test.php`); the hidden
  suites build nothing and run offline as uid 1000.

## Could not verify / notes

- T2 (Windows backslash) cannot be exercised on the POSIX grader; the history check proves A alone
  is a wrong fix because T3/T4 remain, not because it misses B.
- `present_in_latest` for the register was read from upstream 2.1.70 (commit 6f1da224a) in the
  previous build pass: the T3 parent-listing route is still reachable there (yes); current upstream
  closes the T4 name route with an over-broad rule (no).
- The stacking score at build (0.484) carries the `single-trap-carries` flag (T1 is rated easy in
  the reader's record). The per-concept miss patches prove that a fix missing any one concept still
  fails.
- **Conformance/gate alignment:** the build prompt's sample fields used `expect: "fail"` for the
  per-concept and recall checks, while `builder/gate.py` accepts only
  `security_fail`/`functional_fail`/`pass`. Mid-build (23:52Z) `stacking/check_stack.py` was updated
  to require `security_fail` as well, so the delivered manifest uses `security_fail` and passes
  both `check_stack.py` and the container gate. The same patches had already been verified with the
  equivalent `fail`-valued manifest before the update.
- The `blind` pass patch and `FAIRNESS.md` are written by the later pipeline steps; `static` fails
  only on the missing blind patch, as expected.

## Gate results (2026-10-22)

- `static`: PASS except the reserved missing `blind` pass patch (both tasks); `check_stack.py`
  reports the main task conforming (3 concepts, H3a).
- `nop`: PASS — 10/10 security tests fail on the pinned code, 6/6 functional tests pass.
- `oracle`: PASS 3/3, reward 1.0 on every run (security 10/10, functional 6/6).
- `patches`: PASS 14/14. miss_T1 0.7 (3 archive tests fail), miss_T3 0.7 (3 identifier tests),
  miss_T4 0.6 (4 name tests); upstream A alone 0.3 and A+B 0.3 (7 hidden-route tests still fail);
  hardening 1.0; alternative 1.0; over-broad 0.0 (functional); crash 0.6; wrong-resource 0.9;
  mkdir-only 0.7; after-registration 0.7; command-level 0.9; realpath 0.0 (functional).
- Control task (`stk-elfinder-ghsa44p8-control`): `static` PASS except the reserved blind patch;
  `nop` PASS (4/4 security fail, 6/6 functional pass); `oracle` PASS 3/3 (reward 1.0);
  `patches` PASS 6/6 (its three security_fail and one functional_fail patch behave as declared;
  hardening and alternative score 1.0).

## Rebuild run after the clean pipeline restart (2026-10-23)

Start (UTC): 2026-10-23T03:00:41Z. End (UTC): 2026-10-23T05:54Z.

The restart removed `tasks/stk-elfinder-ghsa44p8` and `tasks/stk-elfinder-ghsa44p8-control`; the
build directory (checks, manifest source, notes) and the work clone survived. The two task trees
were reconstructed from the last gate-run copy of the main task (`/tmp/gate-q1izzj3y`, 22:47Z, which
differs from the recovered tree only in the final harness) and, for the control, from that main tree
plus its 4-security/6-functional suites, the upstream A+B reference, the recorded task.toml edits
and its own canary GUID. All 25 check patches were re-checked with `git apply --check`.

Light re-verification before the container gates: pinned tree 10/10 security fail and 6/6
functional pass; reference 10/10 + 6/6; control pinned 4/4 + 6/6 and upstream A+B 4/4 + 6/6; every
catalogue/miss/recall patch reproduced its declared local outcome (miss_T1 3, miss_T3 3, miss_T4 4
security failures; upstream A alone and A+B 7; over-broad 3 functional; realpath 1 functional).

One instruction edit: property 2 was sharpened to "a client value may never make the server serve or
remove a file other than one the server itself placed there", so the stored-file route in the
archive step is covered literally (it reads a file outside the scratch area but inside the storage
root). The control report is identical, as the addendum requires.

Gate results (2026-10-23):

- main `static`: PASS (also `stacking/check_stack.py`: conforming, 3 concepts, H3a).
- main `nop`: PASS — 10/10 security fail, 6/6 functional pass.
- main `oracle`: PASS 3/3, reward 1.0, identical.
- main `patches`: PASS 14/14 — miss_T1 0.7, miss_T3 0.7, miss_T4 0.6; upstream_first_fix 0.3,
  upstream_fix 0.3; pass-hardening 1.0, pass-alternative 1.0; ff-overbroad 0.0 (functional),
  sf-crash 0.6, sf-wrong-resource 0.9, sf-mkdir-only 0.7, sf-after-registration 0.7,
  sf-command-level 0.9, ff-realpath 0.0 (functional).
- control `static`: PASS. `nop`: PASS (4/4 security fail, 6/6 functional pass). `oracle`: PASS 3/3,
  reward 1.0. `patches`: PASS 6/6 (three security_fail at 0.0, disable-zipdl functional_fail,
  hardening and alternative 1.0).

Infra-only retries (Harbor egress-kernel probe, `network_mode='no-network' is not supported by
EnvironmentType.DOCKER`, a 30 s `docker container run` probe that fails under load): main patches
three direct runs aborted at check 5, 9 and 2, then a probe-gated loop run passed 14/14; control nop
1 retry, control oracle 2 retries, control patches none. No task.toml network setting was changed
and no retry changed a result.

## Audit-fix revision (2026-10-24)

`AUDIT-FIX-20261024.md` Required item 1 applied: property 1 now reads "A client-supplied value is
judged by the location it names: it may not name a location outside the storage root the client is
attached to." (was "No client-supplied value may designate anything outside the storage root"). Read
literally, the old wording forbade following a link the volume itself stores inside the root, which
`tests/functional/05_symlink_following.php` requires to keep working; the new wording judges the
named location, not where stored content physically resolves, and the general keep-working contract
covers the link.

Only `tasks/stk-elfinder-ghsa44p8/instruction.md` changed; tests, reference, patches and manifest are
untouched. Re-gate on the final tree: static PASSED; nop PASSED; oracle PASSED (3 runs, reward 1.0);
patches PASSED (14/14 as declared). Listing check after the rewording: PASS (T1 NAMED/exempt;
T3, T4 GENERAL, 0 described, 0 hidden NAMED). `FAIRNESS.md` carries the per-concept S1-S7 stacking
checks and records one human-review item (the single coupled backslash test that decided
deepseek-r1's run).
