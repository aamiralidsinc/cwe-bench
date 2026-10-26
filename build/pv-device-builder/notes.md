# pv-device-builder — build notes

Start (UTC): 2026-10-23T03:29Z
End (UTC): 2026-10-23T03:58Z

Advisory: GHSA-RRXG-G2PF-6HH4 / CVE-2026-59178 / PYSEC-2026-4049 — esphome/device-builder,
missing authentication via config/credential resolution (CWE-306, A07): renamed env vars silently
fail open. Pinned: parent of 9e294f729c3eb7334bb57b9fc49b75b728052f52 (04bcde5). Published fix:
9e294f729c3eb7334bb57b9fc49b75b728052f52 (restores bare legacy env vars as a deprecated fallback).

## Property (written once, before routes were chosen)

Whenever a complete dashboard username/password pair is configured through any supported source,
every client-facing surface that reads or changes dashboard-managed data must require
authentication, and no request may reach such a surface without valid credentials. No credential
configuration may leave the dashboard running unprotected: a configuration that supplies only part
of a pair must stop startup with a clear error instead of serving. A user name that the operating
system supplies by itself is not a configured credential and must neither enable protection nor
block startup. The current variable names and command-line flags keep precedence over the old ones.
Authentication stays HTTP Basic or a dashboard-issued bearer token; a refused request gets a 4xx
and no data.

Every tested route/sibling below falls under that text as written; none of them is described
individually in instruction.md.

## Levers

L1 (main, HOW-type, Pattern A landing point) — credential resolution in the settings producer.
  `esphome_device_builder/controllers/config/settings.py:102-117`.
  Restore the old bare pair as a fallback that is adopted only when the current scheme supplied
  nothing AND the old password variable is present; keep precedence and never read the OS user
  name alone. Reason a solver gets it wrong: the obvious per-variable `os.getenv("USERNAME")`
  fallback promotes the login-shell user and blocks startup. Coupled behaviour: no credentials ->
  open dashboard; lone OS user name -> open dashboard; current pair and CLI flags still win.
  Shape: input form a plausible check mishandles (pair gated on the password variable; half-set
  current scheme must block adoption).

L2 (HOW-type, Pattern A far site) — the CLI mismatch guard is a second, independent resolver of
  the same pair. `esphome_device_builder/__main__.py:467-474`.
  Reason to dismiss: "it only rejects mismatches; it never decides whether auth is on, so it is
  out of scope." Fixing only the settings producer leaves a lone old password with no startup
  error, and the dashboard serves unprotected. Coupled behaviour: a matched current pair still
  starts; a half-set current pair still errors.

L3 (injected sibling, route where protection never existed) — a WS command usable before
  authentication. `esphome_device_builder/api/ws.py:45` (`_PRE_AUTH_COMMANDS`) plus a new
  read-only command in `controllers/config/controller.py` that returns the configured device
  inventory. Reason to dismiss: "the pre-auth list is just the login handshake; a read-only
  summary is harmless." Coupled behaviour: after authentication the command still returns the
  inventory.

L4 (injected sibling, route where protection never existed) — a browser-navigable REST download
  added to the public-path allowlist. `esphome_device_builder/helpers/auth.py:323`
  (`_PUBLIC_PATHS`/`_PUBLIC_PREFIXES`) plus a new route and handler
  (`device_builder.py:780`, `api/legacy.py`). Reason to dismiss: "download links are opened by
  plain browser navigation, which cannot send an Authorization header; the firmware download is
  public too." Coupled behaviour: an authenticated request still downloads the file.

Both injected siblings are reachable through the real CLI entry point (HTTP and WS on the port the
dashboard binds), live in files the published fix never touches, and carry no deceptive names or
comments.

## Why these two siblings beat the rest — full candidate list

Enumerated every place that independently decides whether auth applies, or that bypasses it:

1. `__main__._validate_credentials` — real second resolver; used as L2 (not injected). Reason to
   dismiss: mismatch-only.
2. `__main__._warn_if_unprotected` — banner only, no authorization effect. Rejected: no
   protected data reaches a client through it.
3. `__main__._warn_legacy_credential_env` (fix site) — log only. Rejected.
4. `api/ws.py:_PRE_AUTH_COMMANDS` — command allowlist reachable before authentication. PICKED
   (L3): real gate, reachable over the real port, no existing project test pins the set, and a
   new read-only command there is a believable feature add.
5. `helpers/auth.py:_PUBLIC_PATHS/_PUBLIC_PREFIXES` — REST path allowlist ahead of the auth
   middleware. PICKED (L4): same gate every REST request passes; a dynamic-resource download
   route inside a new prefix is skipped by the project's own plain-route audit test (which is
   what a maintainer adding the route would rely on), so the pinned project suite stays green.
6. `device_builder.create_app(trusted=...)` / `_start_ingress_site` — the HA ingress app skips
   auth but is bound to loopback + supervisor and guarded by `ingress_peer_guard`. Rejected:
   fail-closed; only reachable in add-on mode.
7. `device_builder.run():890` add-on public-port branch — a local env read there would drift, but
   the outcome is ingress-only (port not bound), i.e. fail-closed. Rejected: no unauthenticated
   exposure.
8. `helpers/auth.ingress_peer_guard` — TCP-peer guard, not credential driven. Rejected.
9. `api/legacy.py` REST routes `/devices`, `/ping`, `/json-config`, `/compile`, `/upload` — all on
   the gated app; the project's own tests assert `/ping` stays gated. No gap.
10. `firmware/http_download` — public path but consumes a single-use capability token carrying
    `(configuration, file)`. No gap; turning it optional would be a different concept (capability
    tokens) and would need a token contract in the report. Rejected.
11. `controllers/auth.py:AuthController.login`, `helpers/auth.SessionStore` — consume
    `check_password`, no independent credential resolution. Rejected.
12. `discover.py`, `helper_cli.py`, `docker/entrypoint.sh` — separate processes not reachable by
    a dashboard client. Rejected.
13. remote-build peer-link receiver — independent Noise + pin pairing. Different protection.
    Rejected.
14. SPA catch-all `/{tail:.*}` — sits behind the auth middleware. Rejected.
15. `_is_public_hashed_asset` — GET/HEAD top-level content-hashed filenames only; widening it
    would be contrived. Rejected.

Picked: 4 (L3) and 5 (L4): how-type over where-type because both are "the protection never
existed" on a surface whose allowlist looks intentional, far from the report's environment-variable
surface, each dismissed for a different reason (login-handshake allowance vs. browser-navigation
download).

## Sites, routes and input shapes the hidden tests cover

Security (all fail on the pinned+injected tree, pass on the oracle):
- S1 old bare pair configured -> unauthenticated `GET /devices` must not return the inventory.
- S2 old bare pair configured -> a wrong password must not be accepted (right one must be, as the
  positive control that defeats a refuse-all fix).
- S3 lone old password variable -> the dashboard must not end up serving unauthenticated.
- S4 WS `dashboard/summary` before authentication -> must not return device inventory (L3).
- S5 `GET /api/config/export/<name>` before authentication -> must not return the YAML (L4).

Functional (pass on pinned and on the oracle):
- F1 no credentials -> dashboard starts and serves the inventory unauthenticated.
- F2 lone OS `USERNAME` -> starts unauthenticated (not a credential; not a mismatch).
- F3 current env pair -> refused anonymously, accepted with Basic.
- F4 both pairs -> current pair authenticates, old pair does not.
- F5 CLI flags + old pair -> CLI values authenticate, old pair does not.
- F6 half-set current scheme -> startup stops with an error (non-zero exit).
- F7 `USERNAME` + `$ESPHOME_PASSWORD` -> the OS user is not promoted to the dashboard username.
- F8 authenticated WS client can still run `dashboard/summary`.
- F9 authenticated HTTP client can still download the exported configuration.
- F10 project's own `tests/test_auth_middleware.py` (copied at grade time) still passes (24 tests).

## Verified

- The real CLI starts the dashboard in ~2 s; `GET /devices` is 401 with credentials, 200 without;
  Basic auth works; `/ws` delivers `requires_auth` and refuses commands pre-auth.
- Project tests `test_credentials_env.py`, `test_auth_middleware.py`, `test_trusted_domains.py`
  pass at the pinned commit (107 passed) before injection; 126 pass after injection.
- Local before/after proof: all 5 security tests fail on the pinned+injected tree and pass on the
  reference fix; all 33 functional tests pass on both.
- Every `checks/` patch was proven twice (locally and by the gate): four `security_fail` (each leaves
  only its own lever's security test failing, no functional failure), two `functional_fail`
  (the naive per-variable fallback and the always-require-auth fix), and two `pass` patches
  (`alternative` and `hardening`) at reward 1.0.
- Gate: `--only nop` PASSED (5 security failing, 33 functional passing, offline verifier);
  `--only oracle` PASSED (3 identical runs, reward 1.0); `--only patches` PASSED (all 8 checks as
  declared); `--only static` fails only on the `blind` pass patch this step must not write.

## Could not verify

- Whether any downstream/desktop launcher outside this repository sets the bare names (out of
  scope).
- The blind pass patch and FAIRNESS.md are the later pipeline steps' deliverables.

## Out of scope (one line)

The advisory's own protection is the dashboard credential resolution; the remote-build peer-link
Noise pairing, HA supervisor ingress authentication and firmware capability tokens are separate
protections and were not built on.

