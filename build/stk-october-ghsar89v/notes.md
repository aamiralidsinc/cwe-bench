# stk-october-ghsar89v — build notes

- Start (UTC): 2026-10-26T02:02Z
- End (UTC): 2026-10-26T04:23Z for the build; gate stages continued after that
- Gate: static PASSED; nop PASSED (8/8 security fail on the pinned tree, 101/101 functional pass; reward 0.0);
  oracle PASSED (three runs, each 109/109 and reward 1.0)
- Repo: octobercms/october @ d49266ad90246fcf90565de8ccdcdbad492de0fe (parent of A's first commit)
- Advisories: GHSA-94vp-rmqv-5875 (CVE-2020-15247, fix 4c650bb775ab) and
  GHSA-r89v-cgv7-3jhx (CVE-2020-26231, fix d34fb8ab5110) — H3b, the second is the bypass of the first.

## Levers (one line each)

- T1 (deepseek, advisory route): the CMS Twig environment has no sandbox, so a template expression
  registers a callable on the page/layout object and invokes it — modules/cms/classes/Controller.php:608
  and modules/system/ServiceProvider.php:299, with the extension mechanism at ExtendableTrait:161.
- T2 (both, published-fix far site = B): the event mechanism is a second call path — bind a callable
  (bindEvent/bindEventOnce) and fire it with attacker arguments (Emitter.php:30/41/108).
- T3 (mimo, uncovered upstream, pattern B): the page's storage builder is reachable from a template
  expression and writes a PHP code section into the template's own file (Halcyon Builder::update:382),
  so a later request runs it even though the model save guard would have refused it.

## Design notes

- The reader's record framed the protection as the CMS safe-mode save guard and proposed theme import,
  marketplace install, AutoDatasource and a section-separator shape. I checked those against the pinned
  tree: the section-separator idea does not work (SectionParser::render truncates markup at the last
  separator and wraps code in PHP tags, so a separator inside markup cannot create a code section, and a
  settings value that tries it leaves an unterminated INI quote, which is rejected on load). Theme import
  and marketplace install are trusted whole-package operations under different permissions, and
  AutoDatasource only writes content that came through the model. The published fixes are the Twig
  sandbox, so the stack was rebuilt on the mechanism the advisories actually describe.
- T2 is the exact route of advisory B (bindEvent), which upstream itself shipped as a separate fix.
- T3 is real upstream code untouched by both published fixes; upstream added the storage method names to
  the same policy later (ea67b615e, 2020-12-18), so `upstream_fix.patch` fails the security suite.
- The functional group keeps the coupled values honest: legitimate expressions/partials must render,
  deployed code sections must still run, event binding and the storage API must still work from PHP, and
  safe mode must still refuse saving a new code section.

## Verified

- Every security case executes on the pinned tree and is refused by the reference fix (run locally in the
  built image as the uid-1000 agent, then again by the gate): 6 security cases in nop/oracle plus the four
  T1 shapes; 101 functional cases (94 project CMS unit tests + 7 task cases) pass in both states.
- The project's own CMS suite (tests/unit/cms, 94 tests) passes in the image at the pinned commit
  (asserted during the image build).
- Each check patch was run locally and has the declared outcome: miss_dynamic 4/8, miss_bind 5/8,
  miss_write 7/8, upstream_first_fix 4/8, upstream_fix 7/8 (recall: the stack adds a route), scope_object
  5/8, refuse_all 8/8 security + 95/101 functional, crash_as_refusal 8/8 + 66/101, hardening 8/8 + 101/101.
- The write route was verified end to end with a *fresh PHP process* for the later request (the
  compiled-template cache is per process and keyed by file path).

## Not verified / assumptions

- october/rain is pinned to release 1.0.467 (2020-06-20), the last release before the pinned commit. The
  repository's own modules are autoloaded from modules/ (composer `replace`), so no packaged module copy
  can overwrite the pinned source; the installed tree is the pinned source.
- The advisories publish no payload; the routes were found by reading the pinned tree and confirmed
  behaviourally. Field names (function names, method names) used by the tests are literals in the tests.
- No upstream regression tests exist for either fix in the pinned tree (checked the history between the
  pin and the fix commits).

## Scope note

- Everything here is inside this advisory's own protection (template content must not run PHP under safe
  mode). The system Twig environment is sandboxed by the reference change for fidelity to the published
  fix, but no test drives it (the mail-template path has no object in its render context that a template
  author controls); it is not built on.
