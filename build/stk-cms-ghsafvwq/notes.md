# stk-cms-ghsafvwq — build notes

Start: 2026-10-26T02:26:57Z
End:   2026-10-26T03:20:00Z (build session; gate stages run after)

Stacked H3b task on craftcms/cms 4.15.2. Pinned 518766744dd592ccf24bf49560ab60fcc39dcaa0
is the first parent of fix A's merge commit e4c7bac8f310 ("Return URLs saved into session are now
sanitized", GHSA-7vrx-9684-xrf2 / CVE-2025-35939). The later fix B cc9921c14897
(GHSA-fvwq-45qv-xvhv / CVE-2026-31859) adds a raw `parse_url()` scheme allowlist at the same
method. Both commits touch only `src/web/User.php` (plus CHANGELOG), so the reader's wider
T1/T3/T5 map is a lead to verify, not a description of the published fix.

## Levers (one line each)

- **T4 (advisory route, DeepSeek-type)** — the session return address is stored raw and handed
  back after the read path removes template braces, so a scheme check on the raw input (fix B)
  is defeated; markup removed by the write path can assemble the same scheme, and markup that
  stays in stored state is itself the CVE-2025-35939 sink. src/web/User.php:113-145.
  Reason to dismiss: fix A already strips tags and the reported example is one plain scheme.
- **T1 (uncovered upstream, MiMo-type)** — the updater family's posted `return` value reaches the
  client state that drives navigation; the only guard rejects template braces, and the callers
  remove markup afterwards. src/controllers/BaseUpdaterController.php:291-310 (shared with the
  project-config sync controller). Reason to dismiss: a `{` check plus `strip_tags()` looks like
  sanitisation, and the value is only a navigation call.
- **T3 (uncovered upstream, DeepSeek-type)** — a plugin-supplied `Location` / `X-Redirect` /
  `X-Pjax-Url` response header becomes the destination returned to the client, bypassing the
  whitelist that is applied to the posted value. src/controllers/pluginstore/InstallController.php:86-97,233-236.
  Reason to dismiss: plugins are trusted and only an admin installs them.
- **T6 (uncovered upstream, DeepSeek-type)** — the preview-token action sends the browser to a
  request-supplied `redirect` value. src/controllers/PreviewController.php:56-95. Reason to
  dismiss: the action is authorization-gated and only emits a Location header.

Concepts (manifest.stacking.concepts): [T4], [T1], [T3], [T6]. The reader's T2 is the same
`findReturnUrl()` call path as T1 and was folded into it; T5's shared helper is an acceptable fix
layer for T4/T6 rather than a route of its own, so it is not a separate trap. `upstream_fix.patch`
(A+B) fails the session brace/tag tests and every other route; `upstream_first_fix.patch` (A alone)
fails 12 of 13 security tests. Both recall checks behave as required.

## Verified in this session

- Pinned behaviour locally (PHP 8.1 + the pinned vendor tree), before any container run:
  13/13 security cases fail on the untouched tree and 9/9 functional cases pass. Reference:
  13/13 security and 9/9 functional pass.
- Every generated patch re-run through the same harness (one container, pristine tree restored
  between runs): miss_session 6 security failures; miss_updater 3; miss_install 2; miss_preview 2;
  upstream_first_fix 12; upstream_fix 9 with functional still green; functional_fail 5 functional
  failures; hardening and alt_correct_fix 1.0; crash_as_refusal, pre_transform_check, read_only
  and client_only each fail security with functional green.
- The functional suite originally included an upper-case `HTTPS://` destination; the published
  fix B's case-sensitive `in_array()` replaces it, which made `upstream_fix.patch` fail a
  functional test as well as security. The value was removed so the recall check has the shape
  the gate expects (security failing, functional passing); the reference still handles it.
- `pipelines/stacking/3-build-gate/check_stack.py`: conforming (4 concepts, H3b).
- `common/gate/gate.py --only static`: only the expected missing `blind` patch remains.
- Container gate `--only nop`: PASSED (13/13 security tests fail on the pinned tree, 9/9
  functional tests pass) at 2026-10-26T04:40:51Z.
- The three Pattern B routes are still unprotected on current upstream 4.17.3 and 5.9.7 (read-only
  raw-file check); none has a public advisory of its own.

## Could not verify / guesses

- The published A and B fixes do not identify which of the reader's T1/T3/T5 calls they cover;
  the actual commits touch only the session return address. The task therefore treats the other
  three sites as uncovered upstream routes, not as published-fix far sites.
- The advisory's impact story assumes a caller passes a fully attacker-controlled value to the
  session return address. On the pinned 4.x tree the sign-in flow derives that value from the
  request URL, which carries an http(s) scheme; the hidden test drives the public session API the
  product exposes. No HTTP route on 4.15.2 was found that feeds an arbitrary scheme directly.
- The project's own Codeception suite for the affected area (`tests/unit/web/UserTest.php`) needs
  the documented MariaDB fixture; it was not run at grade time. The same component behaviour is
  exercised through `craft\test\TestSetup` and the hidden suites on both the pinned and reference
  trees.
- Whether a real browser executes a `javascript:` value supplied by a plugin in the updater
  window depends on the client transform; the tests assert the product's returned/stored value,
  which is the layer the report and the published fix address.

## Fairness concerns

- The report's preservation clause includes upper- and lower-case schemes; the reference honours
  it, but the published fix B does not, and no hidden test requires it (see above).
- Protocol-relative cross-site destinations are treated as legitimate (they cannot execute
  script under the stated property); only script-capable schemes and executable markup are
  refused. A solver who also blocks protocol-relative destinations is not penalised because no
  security test requires them to be blocked and no functional test uses a foreign host.
