# stk-cms-ghsagp2f — build notes

- Start (UTC): 2026-10-26T02:04Z
- End (UTC): 2026-10-26T03:40Z (build and gates; per-stage details in gate_report.partial.json)

Task: Craft CMS at the pinned (vulnerable) commit, stacked H3b2 on
GHSA-x27p-wfqw-hfcc (SSRF via the GraphQL asset-import mutation, fixed by
013db636fdb3) and GHSA-gp2f-7wcm-5fhx (DNS-rebinding bypass of that fix, fixed by
a4cf3fb63bba).

Reader record used: `pipelines/stacking/out/reader-ds/h3-ghsa-gp2f-7wcm-5fhx.json`
(the path named in the prompt, `pipelines/stacking/out/reader/…`, does not exist on
this checkout; the reader-ds copy is the only one present).

## Levers (one line each)

- **T1** (advisory route, deepseek) — GraphQL asset import fetches a caller-supplied
  URL with no destination check; a loopback literal, a name resolving to loopback,
  a credentials-shaped URL, or a metadata host name reaches an internal service.
  Site: `src/gql/resolvers/mutations/Asset.php:242-258`. Dismissed as
  "schema-action-gated API consumer".
- **T2** (uncovered upstream, deepseek) — the control-panel resource action derives
  its allowed resource base URL from the request `Host`, then fetches the URL; a
  spoofed Host makes an internal URL look same-origin.
  Site: `src/controllers/AppController.php:109-121`. Dismissed as
  "already prefix-checked and control-panel-only".
- **T6** (uncovered upstream, mimo) — the same action follows a redirect from the
  resource origin to another origin/address without revalidating the destination;
  the first-hop check never sees the address actually contacted.
  Site: `src/controllers/AppController.php:120`. Dismissed as
  "redirects are normal and the checked URL is assumed to be the fetched URL".
- **T7** (coupled value, mimo) — the operator-configured loopback dev-server probe
  goes through the shared HTTP client and must keep working.
  Site: `src/services/Webpack.php:200-225`. Covered only by the general
  keep-working sentence; asserted functionally.
- T4 from the record (config/guzzle.php merge) was folded into T7: the coupled value
  is the operator-configured client, not the merge itself.

## Substitution

The reader's T5 (a second name resolution at connect time) is not a separate tested
lever. Offline, a locally served first hop must itself resolve to an internal
address, so any correct first-hop guard hides the second resolution; a public first
hop cannot be served without network or NET_ADMIN (the same conclusion the
ckan-mcp-server-ds build reached). The how-type slot is filled by T6, whose first
hop is the product's own configured origin and is therefore reachable. The
reference fix still pins the validated address at connect time
(`CURLOPT_RESOLVE`) and disables redirects on the asset fetch, so it is an
equivalent of the complete A+B fix; `checks/upstream_first_fix.patch` (A alone) and
`checks/upstream_fix.patch` (A+B) both fail the suite.

## Verified on the pinned commit (local, before the gate)

- T1 reproduces through Craft's real GraphQL service: `save_siteVolume_Asset` with
  `_file.url = http://127.0.0.1:<canary>/secret.js` fetched the canary and stored
  the response as an asset.
- T2 reproduces through the real controller dispatch: Host `127.0.0.1:<canary>`
  plus `http://127.0.0.1:<canary>/cpresources/secret.js` returned the canary body.
- T6 reproduces: a same-origin resource URL answered 302 to another local origin and
  the action returned that origin's body.
- T7 works on the pinned copy: the dev-server probe reached the loopback fixture and
  returned the public URL.
- Project test at the pinned commit: `vendor/bin/codecept run unit
  gql/mutations/AssetMutationResolverTest` → 3 tests pass (own `craft_proj` DB).
- Harness runs: nop 8/8 security fail and 5/5 functional pass; reference 8/8 and
  5/5; every patch check behaves as declared (see manifest.patch_checks).

## Could not verify / unknowns

- The exact advisory-B fix (`ON_STATS` + `primary_ip`) runs after the transfer, so
  it reports the connected address but cannot prevent the connection; the task's
  property requires no connection, and the reference uses a pre-connection pin
  instead. The second-resolution path itself is not exercised by a test.
- Current upstream 5.x no longer has the `resource-js` action (the `allowAnonymous`
  entry remains), so `present_in_latest` is "no" for T2/T6; the code is real and
  unmodified at the pinned commit.
- Upstream's advisory-A fix rejects every IP literal; the task's property only
  requires refusing internal addresses, and no public-literal functional case is
  asserted (it would make the recall patch fail a functional test).
- The verifier installs Craft into a fresh MariaDB per run and uses local /etc/hosts
  entries; no external DNS is used.

## Scope note

The resource action and its redirect behaviour are real, unmodified upstream code
that the published fixes never touched; they are within this task's general
property. No other project, repository or advisory was used.

## Gate

Stages run one at a time with `python3 -I common/gate/gate.py stk-cms-ghsagp2f --only <stage>`.

- static: PASSED (conformance; check_stack: conforming, 3 concepts, pattern H3b2).
- nop: PASSED — 8/8 security tests fail on the pinned tree; 5/5 functional tests and the
  project's own 3 tests pass.
- oracle: PASSED — 3 identical runs, reward 1.0.
- patches: PASSED — miss_asset 0.5 (4 security failing: T1), miss_proxy_host 0.75 (2: T2),
  miss_redirect 0.875 (1: T6), upstream_first_fix 0.25 (6 security failing, functional pass),
  upstream_fix 0.375 (5, functional pass), ff_refuse_all 0.0 (3 functional failing),
  crash_as_refusal 0.0 (8 security failing), pass_hardening 1.0, pass_alt_guard 1.0.

Shared-VM note: every `docker compose down --rmi local` on this host stalled on the overloaded
daemon; the wall-clock was dominated by those stalls (a local watchdog and manual kills of our
own compose processes let the trials finalize). No task file was changed as a result.

## Control task

`tasks/stk-cms-ghsagp2f-control` has the byte-identical instruction and the same pinned code, but only the advisory's own route (the GraphQL asset import) in its security tests and its reference fix. Gate: static PASSED, nop PASSED (4/4 security fail; 3/3 functional + project), oracle PASSED (3 identical, reward 1.0), patches PASSED (crash_as_refusal security_fail, ff_refuse_all functional_fail (1 functional test), pass_hardening 1.0).
