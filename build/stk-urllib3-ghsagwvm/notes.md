# stk-urllib3-ghsagwvm — build notes

Start (UTC): 2026-10-26T12:22:09Z
End (UTC): see end_utc.txt

Candidate: h3-ghsa-gwvm-45gx-3cf8 (pattern H3b2, stacked).
Advisories: GHSA-www2-v7xj-xrc6 (CVE-2018-20060, fix 560bd227b90f) and GHSA-gwvm-45gx-3cf8
(CVE-2018-25091, fix adb358f8e068, the case-insensitive follow-up).
Pinned commit: c4f123dcdcad3582561373278d2772f819ec3cb8 = first parent of 560bd227.

The reader record was read from `pipelines/stacking/out/reader-ds/h3-ghsa-gwvm-45gx-3cf8.json`
(the path named in the prompt, `pipelines/stacking/out/reader/…`, does not exist; the ds run does).

## Levers (one line each)

- T1 (A, advisory route, both): the request manager's redirect loop replays the caller's headers to
  the target with no origin comparison — urllib3/poolmanager.py:316,328,349.
- T2 (A, published-fix far site, deepseek): the same guard must withhold every credential header and
  every source of them (client-configured headers, further hops), not only the header the advisory
  names — urllib3/poolmanager.py:316,349.
- T5 (B, uncovered upstream, mimo): what counts as another origin — a same-host port change leaves
  it, a relative Location or a differently-cased host stays on it — urllib3/poolmanager.py:328,349,
  urllib3/connectionpool.py:428-447.
- T4 (B, uncovered upstream, deepseek): the connection pool's own redirect loop, documented for
  `assert_same_host=False` proxy use, re-sends the headers with no origin check —
  urllib3/connectionpool.py:682-708.
- T7 (B, uncovered upstream, deepseek): the URLFetch-backed manager lets the platform follow
  redirects, so every hop replays the headers unseen — urllib3/contrib/appengine.py:141-201.

Concepts: {T1,T2,T5} = the manager guard; {T4} = the pool's redirect loop; {T7} = the URLFetch
implementation.

## Design deviation from the reader's record

The record's design chose T1, T2, T3, T4, T6. Two were changed, both verified against the pinned
code and the gate's own rules:

- **T3 (retry-carried removal set) dropped.** Its only distinguishing behaviour is a *configurable*
  removal set (`Retry(remove_headers_on_redirect=...)`). That parameter does not exist at the pin,
  so a hidden test can only drive it by naming it, and naming it in instruction.md makes T3 NAMED
  for the listing check (one NAMED hidden trap = FAIL). Without the name the tests would require
  the solver to guess an identifier — unfair. The reference fix still implements the natural
  retry-level policy in `checks/pass-hardening.patch`, but no test depends on it.
- **T6 (ProxyManager over-strip) dropped as a lever.** Upstream's own fix (560bd227) keys the origin
  check on the connection pool, so it *strips* credentials on a same-origin redirect through a
  plain-HTTP proxy. Any functional test for that must-keep would therefore fail
  `checks/upstream_first_fix.patch` and `checks/upstream_fix.patch`, which the gate requires to be
  `security_fail` with *all functional tests passing*. The proxy route is still covered as a
  security test (cross-origin through a proxy); the same-origin proxy value is not tested. This is
  a recorded fairness gap: a solver who copies upstream's pool-keyed test passes the suite.
- **T7 added** in their place: a real second redirect-following implementation, gradeable with a
  URLFetch stand-in.

## Verified

- Pinned behaviour, end to end, with local recording servers: manager cross-host/cross-port redirect
  leaks Authorization and Cookie; same-origin relative and mixed-case-host redirects keep them;
  client-configured credentials leak; the connection-pool proxy route leaks; the URLFetch manager
  leaks (the stand-in follows like the platform and carries headers).
- Reference fix (`solution/fix.patch`): 11/11 security pass, 10/10 functional pass, project suite
  121/121 (test_retry, test_poolmanager, test_proxymanager, test_connectionpool,
  with_dummyserver/test_poolmanager).
- Pinned: 11/11 security fail, 10/10 functional pass.
- Every check patch, run locally in the pinned worktree: miss_manager_guard 7 security fail /
  functional pass; miss_connection_pool 2 fail / pass; miss_appengine 2 fail / pass;
  upstream_first_fix 6 fail / pass; upstream_fix 6 fail / pass; sf-port-blind-compare 6 fail / pass;
  ff-refuse-all 5 functional fail; sf-crash-as-refusal 1 functional fail (+ project); ff-adjacent-api
  4 project tests fail (functional group); pass-hardening and pass-alt 1.0.
- Control task: pinned 5/5 security fail + 10/10 functional pass; reference (fix A alone) 15/15 and
  121/121; sf-host-only 3 security fail; ff-strip-all and sf-crash functional fail; pass patches 1.0.

## Could not verify / open items

- The record's `unverified` note guessed GHSA-gwvm-45gx-3cf8 was the 2023 Cookie advisory. The OSV
  record and the fix commit 560bd227/adb358f8 pair show it is the 2023 republication of the
  case-insensitive follow-up to CVE-2018-20060. No Cookie advisory is involved; T2 rests on the
  task's general property, not on a published fix, and is labelled `published_fix_far_site` because
  the fix's own removal set is where the value would belong.
- Header-name case (`authorization` vs `Authorization`) is the published B fix, but a pure spelling
  variant is excluded from levers by the build rules; it is untested (the reference matches
  case-insensitively anyway).
- The connection-pool route is only observable when the pool is used to reach foreign hosts (a
  forward proxy); a single-host pool's cross-host redirect is sent to the pool itself, which is why
  the test drives the documented `assert_same_host=False` use through a forward-proxy stand-in.
- The URLFetch stand-in is our model of the platform service (it follows redirects and carries the
  same headers). A fix that disables the platform's following and follows manually passes; a fix
  that leaves following to the platform cannot pass. Real `google.appengine.api` is unavailable on
  Python 3, so the project's own App Engine tests do not run.
- The shared-header aliasing risk (deleting from `PoolManager(headers=...)` in place) is not tested:
  upstream's own fix regresses it (`RequestMethods.request_encode_url` passes `self.headers` in
  `kw`, so the published `pop` mutates the client's configured headers), and a functional test for it
  would fail both recall checks. The reference fix copies before removing.
- Current upstream (origin/main 8883fd90) now strips in `connectionpool.py:911-918` and compares the
  request URL's origin in `poolmanager.py:504-513`; `contrib/appengine.py` has been removed. So T4
  and T5 are closed in 2026 upstream and T7's code no longer exists — see the register rows.

## Fairness concerns I see myself

- The manager guard (T1/T2/T5) and the connection-pool guard (T4) are one idea applied twice; a
  solver who greps for the redirect recursion finds both quickly. T7 is the real second
  implementation and needs a blind solve to produce equivalent manual following.
- The suite does not catch an over-broad pool-keyed origin test (T6), because the published fix has
  that same behaviour. Recorded above.
- `checks/upstream_fix.patch` also applies the case-insensitivity fix (B); it changes nothing in the
  security outcome (Cookie, the pool route and the URLFetch route still fail), which is what the
  recall check asserts.
