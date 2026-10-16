# rclone build notes (SLUG = rclone, CWE-287, GHSA-xwwr-4h3p-r22c)

## Verified against the code (not trusted from the candidate row)

- **Flaw.** With `rclone serve s3 --auth-proxy <prog>` and no `--auth-key`, the
  server (cmd/serve/s3/server.go) runs an `authPairMiddleware` that, per request,
  registers the *client-presented* access key ID in gofakes3's key store with an
  **empty** secret (`ws.s3Secret`, which is empty when `--auth-key` is unset).
  gofakes3 then verifies the request's SigV4 signature against that empty secret.
  An S3 client never sends its secret, only a signature made with it, so anyone
  can sign for any proxy-known access key ID with an empty secret and be let in.
  The separate `proxyAuthMiddleware` only *logs* auth errors and always calls
  `next`, so gofakes3 is the real gate - and it has been fed an attacker-chosen
  empty secret. Reproduced against the compiled binary: empty-secret requests for
  alice/bob return 200/204 and leak/modify the victim's objects; real-secret
  requests are (on the vulnerable code) *rejected* because the registered secret
  is empty.

- **Candidate judgements, checked.** S1 multi-site = **no** (confirmed: one auth
  gate; all S3 operations flow through it). S2 cause-in-another-layer = **yes**
  (the failing check lives in the gofakes3 dependency; the bad state is created
  earlier by the rclone middleware). S7 over-broad-breaks-legit = **yes**
  (refusing to run proxy mode, or never registering a key, breaks legitimate
  proxy-only deployments). The entry_point_GUESS and flaw_one_line were accurate.

- **Fix.** The upstream fix verifies each request's signature against the secret
  the proxy returns for the access key ID (new `Proxy.CallAccessKey` +
  `signature.V4SignVerifyWithSecret`), denies on failure, and never registers the
  secret with gofakes3. The reference `fix.patch` is that commit reduced to the
  three behavioural source files. Built from the vulnerable parent + this patch,
  all attacks return 403 and legitimate real-secret clients are served (verified).

## The check patches (all built and run against the harness)

- `shallow_wrong_layer.patch` (**security_fail**): takes the correct plumbing
  (upstream proxy.go, so the real secret is available) but adds the signature
  check inside the `auth` helper whose error the surrounding middleware ignores,
  leaving `authPairMiddleware` + gofakes3 as the real gate. This is the S2 trap:
  a check is "added" but not where the decision is made. Result: security 0/5
  (every attack still succeeds), functional 5/5.
- `disable_feature.patch` (**functional_fail**): the candidate's #1 tempting
  over-broad fix - refuse to start serve s3 in proxy mode without `--auth-key`.
  The proxy server never comes up, so the proxy functional tests (which need it
  answering) fail. Result: functional 2/5.
- `alt_keystore_fix.patch` (**pass**): a correct fix at a *different layer* than
  upstream - it registers the proxy-supplied real secret in gofakes3's own key
  store (`AddAuthKeys`) and lets gofakes3 verify, denying when the proxy rejects
  the key. Result: 10/10, reward 1.0. This proves the tests do not hard-code the
  shape of the upstream patch.

## No-network design

- The S3 server (`rclone serve s3`), the auth-proxy helper program and the HTTP
  test client all run on localhost. The backends are local directories under
  `/data`. No real remote or internet access at run time.
- The rclone binary and all Go modules are baked into the image; the verifier
  rebuilds rclone from `/app` offline (`GOPROXY=off`, `GOTOOLCHAIN=local`),
  recompiling only the packages the solver changed via the baked build cache.

## Inherent limitation / honest caveat

- The vulnerable server accepts ONLY an empty secret (it registers an empty
  secret); the fixed server accepts ONLY the real per-user secret. The correct
  credential therefore *differs* between the vulnerable and fixed states, so a
  positive auth-proxy request (one that returns 200) cannot pass on BOTH - it is
  mathematically impossible to have a 200-returning proxy functional test that is
  invariant across the fix. The positive functional coverage is therefore on the
  static-key (`--auth-key`, non-proxy) serving path, which the fix leaves
  unchanged and which a careless fix to the shared serve-s3 code could still
  break. The proxy functional tests assert invariant denials (wrong secret, no
  auth, unknown key) plus that the server stays up and answering - which is what
  catches the over-broad `disable_feature` fix. Consequence: a hypothetical fix
  that leaves the server running but denies *every* proxy request would pass the
  proxy functional tests (all are denials); it is not among the check patches
  because it cannot be distinguished from a correct fix by any cross-version
  functional test for this vulnerability. The security_fail and functional_fail
  checks both behave correctly and the gate passes.

## Host validation (outside the gate, for fast iteration)

Built the rclone binary at the vulnerable parent, the fix commit, and with each
check patch, and drove the task harness against each:
vulnerable -> security 0/5, functional 5/5 (reward 0.0);
fix commit / reference patch -> 10/10 (reward 1.0);
shallow_wrong_layer -> security 0/5, functional 5/5;
disable_feature -> functional 2/5;
alt_keystore_fix -> 10/10 (reward 1.0).
The gate re-runs all of this inside Docker via Harbor.

## 2026-10-16 test repair

Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Earlier today (before this pass) the tests
already gained `TestS3ProxyAliceCorrectSecretServed`, `TestS3ProxyBobCorrectSecretServed`
(GET only), `TestS3ProxyNoSecretRefused` (carol: known to the proxy, no secret; signed with
"", the key ID and md5(key ID)), the `reject_all_proxy.patch` check, and the instruction
sentence naming `_secret_access_key`.

Flagged items and decisions:
- deepseek-r11 (lenient: proxy returning no secret; key-ID / md5 fallback) - **already fixed**
  by `TestS3ProxyNoSecretRefused` and the `_secret_access_key` instruction sentence. Optional
  "static --auth-key secret must not authenticate a proxy identity": **skip** - the instruction
  defines proxy mode as started without a static key pair, so `--auth-key` + `--auth-proxy`
  together is outside what it promises.
- deepseek-r4, deepseek-seq1, mimo-r1 (no positive proxy-mode test; deny-all fix scored 1.0) -
  **already fixed** (correct-secret GET tests + `reject_all_proxy.patch`, security_fail).
- deepseek-r21 (secret rotation / revocation while cached) - **skip**: the instruction states
  no caching or revocation behaviour; it comes from the upstream design only.
- mimo-r21 / our notes (correct-secret tests check GET only) - **fixed**: added
  `TestS3ProxyAliceCorrectSecretPutServed` (PUT as alice with her real secret: any 2xx, the
  object is on disk at /data/alice/alicebucket/alice-upload.txt with the sent content, and
  reads back over S3) and `TestS3ProxyAliceCorrectSecretDeleteServed` (DELETE of an object
  seeded in TestMain before the server starts: any 2xx, and the file is gone from disk).
  Fair: the instruction says a client signing with the correct secret must be served and that
  the property holds for all S3 operations (it names GET, PUT and DELETE). No product helpers;
  side effects are checked on the backend directory by the test itself.

New patch check: `checks/reads_only_proxy.patch` (security_fail) - the reference fix plus a
refusal of every non-GET/HEAD request in auth-proxy mode after the signature verified. Fails
exactly the two new tests (reward 0.8). No instruction change in this pass.

Gate (`build/slot.py 3 -- python3 -I builder/gate.py rclone`): **PASSED**
(log `gate-20261016-putdelete.log`). nop security 10/10 failing; oracle 1.0 twice;
alt_keystore_fix (pass) 1.0; shallow_wrong_layer, disable_feature, reject_all_proxy,
reads_only_proxy all fail as expected. Warnings only: no hardening / blind pass patches
(task predates 2026-10-16).

Regrade (all runs with saved final code were at 1.0; deepseek-seq1 `rclone__a4P8Fc2` and
mimo-r1 `rclone__q4t49md` have no `final-code/changes.patch` and cannot be regraded):

| trial | old | new | failing tests |
|---|---|---|---|
| rclone-deepseek-r11 / rclone__rEMTRVZ | 1.0 | 0.9 | security::TestS3ProxyNoSecretRefused |
| rclone-deepseek-r21 / rclone__agcsccS | 1.0 | 1.0 | - |
| rclone-deepseek-r4 / rclone__3SXNjrF | 1.0 | 1.0 | - |
| rclone-mimo-r11 / rclone__L5CYjmw | 1.0 | 1.0 | - |
| rclone-mimo-r21 / rclone__ByW3teV | 1.0 | 1.0 | - |

deepseek-r11 drop is a real defect: its `verificationSecrets` falls back to the access key ID
and md5(access key ID) as the secret when the proxy returns none (and to any other non-protocol
config value), so carol signed with her own key ID was served alice's file (HTTP 200,
"ALICE CONFIDENTIAL FILE"). The drop comes from the earlier no-secret test, not the new
PUT/DELETE tests; no run refused correct-secret writes.
