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
