# stk-siyuan-ghsa4mx9 — build notes

- Start (UTC): 2026-10-23T08:02:32Z (rebuild of the interrupted first attempt; see "Prior attempt")
- End (UTC): 2026-10-23T09:28:46Z
- Pinned commit: 285f7c216a452f0cb8c573b64be26c9ff692d0ad — exactly the parent of A's first fix
  commit. `git cat-file -p d68bd5a79391742b3cb2e14d892bdd9997064927` prints
  `parent 285f7c216a452f0cb8c573b64be26c9ff692d0ad`. Neither fix is in the checkout:
  `SanitizeSVG` does not exist anywhere in `kernel/`, and the only helper is `RemoveScriptsInSVG`.
- Published fixes: A d68bd5a79391742b3cb2e14d892bdd9997064927 (GHSA-6865-qjcf-286f); B
  d01d561875d4f744e9f6232f1d4831e3642b8696 (GHSA-4mx9-3c2h-hwhg), authored on a later tree (its
  parent is bf2984699279). The combined recall patch reproduces A, then B's semantic change (the
  data: URI denylist becomes a raster-image allowlist).
- Entry point: HTTP GET /api/icon/getDynamicIcon?type=8 (unauthenticated) and the authenticated
  file routes that hand a stored SVG to a client (/assets, /emojis, /history, /repo/diff). Every case
  is driven in-process with httptest against the real handler; the role the authentication layer
  sets is put on the gin context, and the real CheckAuth / CheckAdminRole middleware runs. No
  external network and no database at test time.

## Levers

- T2 (concept C1, advisory route, `both`): the text value is interpolated into the generated SVG
  and only elements named exactly `script` are stripped, so an event-handler attribute, a
  `javascript:` link, a markup-bearing `data:` document reference, an embedding element or a
  namespace-prefixed script element supplied as text comes back live. `kernel/api/icon.go:167`,
  `kernel/api/icon.go:579-584`, `kernel/util/misc.go:235-272`; it is the reported route.
- T3 (concept C1, published-fix far site, `both`): the same weak helper guards the route that
  serves uploaded SVG assets (`kernel/server/serve.go:612-628`); reason to dismiss: it is behind
  CheckAuth and serves the workspace owner's own uploaded files, and a fix that only handles the
  reported text value leaves it open.
- T4 (concept C2, uncovered_upstream, DeepSeek-type): `/history/*path` and `/repo/diff/*path` pass a
  stored file straight to `http.ServeFile` (`kernel/server/serve.go:605-609,649-654`); reason to
  dismiss: administrator-only routes serving the owner's own snapshots, never mentioned by the
  report. Both published fixes leave them untouched.
- T5 (concept C3, uncovered_upstream, DeepSeek-type): custom emoji files are served by the router's
  static handler (`kernel/server/serve.go:354-357`), so the SVG path never runs; reason to dismiss:
  authenticated route, emoji files are normally embedded through an image element. Untouched by
  both published fixes.
- T7 (concept C1, injection_room, MiMo-type, how-mechanism): the helper compares the parser's raw
  tag name with `script`; a namespace-prefixed element (`svg:script`) keeps its prefix in `Node.Data`
  and is re-emitted, where an XML parser resolves it as a script element. `kernel/util/misc.go:237`
  and `:250`. The coupled must-keep value is a harmless prefixed element and an `xlink:href="https:`
  link in the legitimate document, which a broad element/attribute-name filter would destroy.

Concepts: C1 = [T2, T3, T7] (one guard and where it runs), C2 = [T4], C3 = [T5].
DeepSeek-type: T4, T5. MiMo-type: T7. Both-type: T2, T3.

## Gate

- 2026-10-24 (after the fairness revision; each stage run with `python3 -I builder/gate.py
  stk-siyuan-ghsa4mx9 --only <stage>`):
  - static: PASSED.
  - nop: PASSED — 9 security tests fail on the pinned tree, 9 functional tests pass, with the serve
    fixture now driving production's engine constructor.
  - oracle: PASSED — three runs, reward 1.0, identical security/functional maps.
  - patches: PASSED — 11/11 executed checks (blind.patch is produced later by run_blindfix):
    miss_sanitizer 6 security failing, miss_serve_history 2, miss_emoji 1, crash-as-refusal 9,
    upstream_first_fix 6, upstream_fix 5; ff-refuse-all 6 functional failing, ff-strip-links 4;
    fix.patch, pass-alt, pass-hardening and the new pass-engine all 1.0; every functional test passes
    wherever a security test is expected to fail.
- 2026-10-23 (pre-revision; kept for history): static, nop, oracle and patches all PASSED, 10/10
  checks.
- Control task gate: static, nop, oracle and patches all PASSED (see below).
- Each `--only` run rewrites gate_report.partial.json, so the file left on disk reflects the last
  stage (the post-edit static re-check); the per-stage logs are kept under
  build/stk-siyuan-ghsa4mx9/evidence/20261023-stage-{nop,oracle,patches,control}.log. The pipeline's
  own full `gate.py stk-siyuan-ghsa4mx9` run writes the authoritative gate_report.json.

## Verified locally (pinned worktree, go test -vet=off)

- nop: 9/9 hidden security tests fail (5 icon + 4 server routes), 9/9 hidden functional pass.
- oracle (solution/fix.patch): 9/9 security and 9/9 functional pass.
- Every check patch run through the same suites:
  - miss_sanitizer (misses T2/T3/T7): 5 icon security tests and the asset security test fail;
    functional pass.
  - miss_serve_history (misses T4): only the history and repo-diff security tests fail; functional
    pass.
  - miss_emoji (misses T5): only the emoji security test fails; functional pass.
  - crash-as-refusal: every security test fails with a server error; functional pass.
  - ff-refuse-all: security tests pass by clean refusal; functional fail.
  - ff-strip-links: security tests pass; functional fail (https and xlink links lost).
  - pass-hardening and pass-alt: both sweep all 18 tests.
  - upstream_first_fix (A alone) and upstream_fix (A+B): security tests still fail (the asset and the
    three route tests; A+B additionally leaves the prefixed-script test failing); functional pass.
- Control task (stk-siyuan-ghsa4mx9-control): gate green — static PASSED, nop PASSED (5/5 icon
  security tests fail on the pinned tree, 5/5 functional pass), oracle PASSED (2/2 runs at 1.0),
  patches PASSED (control_miss_content leaves 2 security tests failing with functional passing;
  control_overbroad breaks 4 functional tests). The control reference is the escaping design applied
  to the text value at the final interpolation.
  The control's 5/5 functional count is met by two extra legitimate-use cases: a date badge renders
  without active content, and a named palette colour still paints the badge.
- The project has no tests for kernel/util, kernel/server or kernel/api at the pin (the only kernel
  test file is model/asset_content_test.go, a PDF parser test unrelated to this area). The packages
  are compiled with `go test -vet=off -run '^$'` at image build and by the verifier.

## Fairness revision 2026-10-24 (audit AUDIT-FIX-20261024.md)

- Defect: `tests/support/zz_stk_serve_support_test.go` built a bare `gin.New()` engine, so a fix
  placed in the middleware chain production `Serve()` installs could never run. The 2026-10-23
  deepseek run hardened the icon/asset sinks and left `/emojis`, `/history`, `/repo/diff` to an
  engine middleware, then failed those three tests (6/9) although the same middleware covers them
  in the real server.
- Fix (audit option (a)): `environment/engine-harness.patch` extracts the engine construction and
  middleware chain `Serve()` already ran into `newGinServer(cookieKey string) *gin.Engine`; `Serve()`
  calls it and is otherwise byte-identical. It is a behaviour-preserving refactor (same engine
  settings, middleware order, session store, no route and no guard added), so the pinned code is
  still vulnerable.
- The serve fixture calls `newGinServer`, then appends the role setter (the JWT middleware would
  otherwise leave the role it derives from the request) and registers the three route functions.
  Route-level assertions are unchanged.
- Evidence that both layers pass: `solution/fix.patch` (per-sink) scores 1.0; the new
  `checks/pass-engine.patch` (icon sanitised at the sink, `/emojis`, `/history`, `/repo/diff` left
  to a response-sanitising middleware installed in `newGinServer`) also scores 1.0. Pinned code still
  fails all 9 security tests; every existing check patch keeps its declared outcome.
- Residual: the icon fixture still builds a bare engine (the icon tests live in package `api`, which
  cannot call `server.newGinServer` without an import cycle), so an engine-middleware-only guard is
  not exercised by the icon cases. The reported route's reference design sanitises at the sink and
  passes; the engine design passes all four serve cases. Recorded in FAIRNESS.md.
- `instruction.md` and `solution/fix.patch` were not changed, per the audit.

## Instruction fairfix 2026-10-24 (audit AUDIT-FIX-20261024.md)

- Defect (one Required item): the Required-properties sentence "nothing in it may run script, embed
  another document, or cause a document that is not an image to be loaded", read literally, also
  forbids the ordinary navigation links (`href="https://..."`, `xlink:href="https://..."`) that
  `TestFunc_{Asset,Emoji,History,RepoDiff}SvgKeepsNonExecutableContent` keeps. A correct fix could
  not satisfy the security rule and those functional tests at once.
- Fix: reworded over the protected outcome, with no attribute, scheme, element or route named:
  "it may not run script, and it may not embed or inline-load another document's active content
  into the page. Ordinary navigation links and raster images stay as they are." The setting-off
  scope, the text-is-content rule, the refusal allowance and both keep-working clauses are
  unchanged.
- Only `instruction.md` changed. Tests, reference fix, environment harness, manifest patch_checks
  and checks/*.patch are untouched. `FAIRNESS.md` §1, S1/S2/S5 rows and the verdict were refreshed
  to the new wording, and a fairfix note 2 added.
- Gate re-run after the edit: static PASSED, nop PASSED, oracle PASSED, patches PASSED.
- Follow-up outside this fairfix: `run_fairfix_stack.sh` copies the new instruction to
  `stk-siyuan-ghsa4mx9-control` (rule 13) and re-runs `stacking/run_listing_check.sh`.

## Could not verify

- Browser execution of the namespace-prefixed element was not run in a browser. What was verified
  in-process: the pinned parser keeps `svg:script` as `Data="svg:script"`, the helper compares that
  name for equality with `script` and keeps the node, `html.Render` re-emits `<svg:script>` together
  with any `xmlns:svg` declaration, and a local-name match removes it.
- Whether a non-administrator can place an SVG under data/emojis: no upload route was traced. The
  tests only establish the served-document property for a file that exists there.
- Real-world harm of the administrator-only history and repo-diff routes: the property is stated
  over the document served, and the routes are reachable by the administrator role the tests set.
- Fix B was authored on a later tree; it is reproduced by its semantic change (data: allowlist), not
  by applying the commit.
- `present_in_latest` for the uncovered routes: the register rows were written by the first attempt
  (same pinned tree), which recorded T4 as `no` (current upstream still serves the bytes but forces
  an attachment disposition for non-raster types, so the document is no longer rendered inline) and
  T5 as `yes` (the emoji static handler still returns an SVG inline). This rebuild did not re-read
  upstream; those two values were not re-checked.

## Fairness concerns

- The kept-working clause is tested functionally: https links, `xlink:href` https links, inline
  styles, a harmless namespace-prefixed element and data:image/png inside stored SVGs must survive;
  plain text, CJK, "A&B" and the template form of a text icon must still render; non-SVG files must
  be byte-identical; and the documented SVG-script setting must return documents verbatim. An
  over-broad sanitiser fails these (ff-strip-links, ff-refuse-all).
- The text icon may be fixed either by escaping the text value at the final interpolation or by
  sanitising the generated document; the functional suite deliberately does not require markup
  inside the text value to be preserved, so both designs pass (pass-alt demonstrates the escaping
  design).
- T4 and T5 are administrator/authenticated routes. The task's property is about every SVG document
  the kernel returns, and the instruction says so generally; a reviewer may still consider the
  real-world attacker model for T4 weak. This was the reader's chosen DeepSeek-type lever.
- The score at build (reader design, 4 concepts): 0.092, p_fail3 deepseek 0.442, mimo 0.208,
  score_without_hardest 0.011, flagged `single-trap-carries` (T7 is the hardest concept). The built
  grouping makes T7 part of the sanitiser concept; the three concept-miss patches show that no
  single concept carries the task: fixing any two still leaves the remaining one's tests failing.
- Effort: seven edit sites across three files (helper, icon sink, asset sink, emoji route, history
  route, repo-diff route); a careful engineer who knows where to look reaches them in roughly 45-60
  minutes.

## Prior attempt

- A first build of the same design ran 00:53-02:19 UTC and produced the check patches now reused
  here. Its static stage failed on a self-inflicted leak term (`getDynamicIcon`, which the report
  legitimately names as part of the public API path); the patches stage died on the shared-VM
  egress-probe flake (`network_mode='no-network' is not supported`). The task tree was recreated
  from the recovered reference and hidden suites; the instruction no longer lists `getDynamicIcon`
  as a leak term.

## Second audit repair 2026-10-24 (audit AUDIT-FIX-20261024.md, second repair)

- Required 1 (functional test vs instruction): `TestFunc_DynamicIconServesScriptsWhenSettingEnabled`
  required caller-supplied `<script>` text to come back raw with the setting on, contradicting
  "Text a caller supplies to the icon API is content, never markup", which the instruction states
  without a setting condition. The test is replaced by
  `TestFunc_DynamicIconKeepsTextVisibleWhenSettingEnabled`, which keeps the setting-on case but
  asserts only that plain text (`A`, `你`, `A&B`) still renders. The unconditional caller-text
  escaping requirement is enforced by the new security case
  `TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled` (setting on; caller text with a
  script; `stkAssertNeutralised` accepts a 4xx or a neutralised 200). It is a security, not a
  functional, case because a functional test must pass on the pinned tree (gate nop).
- Reference: `generateTypeEightSVG` now runs `html.EscapeString(content)` in every mode (after the
  template expansion), so the setting-on path cannot emit caller markup. `solution/fix.patch` and
  the alternative passes `pass-alt`, `pass-hardening`, `pass-engine` were regenerated from the
  engine-harness baseline. `miss_serve_history` and `miss_emoji` also carry the escape so each
  still isolates its own concept.
- Required 2 (checker stricter than the instruction): both copies of `stkActiveSVGContent` now
  flag a `foreignObject` only when its subtree carries active content (script, event handler,
  script-scheme / non-raster `data:` reference, or `iframe`/`object`/`embed`). An inert
  `foreignObject` is accepted. Verified in-process with an inert document and five active variants.
- Required 3: `manifest.traps[T2]` gained the new security test and the renamed functional test;
  `status` and an `audit_fix_20261024_second` block record the repair.
- Fixture repair (flagged by FAIRNESS.md, cheap and safe): `stkLegitSVGDocument` declares
  `xmlns:svg`, so a correct fix that parses the SVG namespace strictly is not failed by a
  malformed legitimate fixture.
- `instruction.md` was not changed (the audit forbade it), so no listing check is triggered by this
  repair.
- Local in-process verification (pinned worktree, `go test -vet=off`): nop = 10 security fail / 9
  functional pass; fix.patch, pass-alt, pass-hardening and pass-engine = 19/19; miss_serve_history
  leaves only history/repo-diff red; miss_emoji only emoji; miss_sanitizer all six C1 icon/asset
  tests red; crash-as-refusal leaves all ten security red with functional passing; ff-refuse-all
  and ff-strip-links fail functional; upstream_first_fix and upstream_fix still fail security.

### Gate re-run after the second audit repair (2026-10-25)

Each stage run with `python3 -I builder/gate.py stk-siyuan-ghsa4mx9 --only <stage>`:

- static: PASSED.
- nop: PASSED — 10 security tests fail on the pinned tree, 9 functional tests pass.
- oracle: PASSED — 3/3 trials reward 1.0, identical (10/10 security, 9/9 functional).
- patches: PASSED — 11/11 executed checks. miss_sanitizer 7 security failing (6 icon + asset),
  miss_serve_history 2, miss_emoji 1, crash-as-refusal 10, upstream_first_fix 7, upstream_fix 6;
  ff-refuse-all 6 functional failing, ff-strip-links 4; fix.patch, pass-alt, pass-hardening and
  pass-engine all 1.0. Every functional test passes wherever a security test is expected to fail.
  The first patches run hit the known shared-VM Harbor startup flake
  (`ValueError: network_mode='allowlist' is not supported`, the egress-probe timeout under load)
  on chk-pass-engine only; the stage was re-run with `GATE_PARALLEL=3` and passed 11/11. No task
  file was changed to work around it.
