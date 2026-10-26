# anycable-ds — build notes

- Start (UTC): 2026-10-24T05:27:52Z
- End (UTC): 2026-10-24T08:45:00Z (gate stages finished 08:40Z)
- Candidate: anycable/anycable, pinned d73d4c8eecbaad344a7826b8b58617d33a412cb6, published fix 201c67e99e463ed63bd6b345562f4c458385fcee.
- Advisory family: GHSA-W72W-9QMJ-C9QM / CVE-2026-63406 / GO-2026-6529 (CWE-798 + CWE-312).
- Pattern B, injected track, strict gate.

## Security property (written once, before routes)

Telemetry is opt-in. The server must not send anything to the telemetry service unless this
deployment has been given its own telemetry token; a value compiled into the product or shipped as
a default is not the deployment's own. Nothing sent may contain, encode or be derived from any
other secret or credential value the deployment configured, in whole or in part and through any
transformation. Reporting only whether a secret is configured is allowed.

The instruction states this invariant and no route. Every route and sibling below falls under it as
written.

## Levers

1. **T1 base / reported** — opt-out default plus a shared compiled-in credential; emptying the
   default is not enough because the sender accepts a token-less tracker.
   where: telemetry/config.go:12-16, telemetry/telemetry.go:56-83, cli/cli.go:318-325.
   dismiss: "Send already omits Authorization for an empty token, so token-less telemetry is
   supported; just remove the hardcoded default." how-type-ish (the fix must understand that the
   gate and the constructor are separate layers).
2. **T2 main, Pattern B uncovered route (real upstream, unmodified)** — the cluster fingerprint is
   an unsalted SHA-256 over ANYCABLE* env *values* (incl. ANYCABLE_SECRET and other credentials),
   raw CLI argument values (incl. --secret, --redis_url) and the whole config file contents, and it
   is sent with every event when telemetry is enabled. The published fix never touches it.
   where: telemetry/telemetry.go:320-421 (clusterFingerprint / anycableEnvVarsList /
   anycableCLIArgs / anycableFileConfig), sent at telemetry/telemetry.go:125.
   dismiss: "it is only a one-way hash / an anonymous cluster id; the docs say env vars are not
   collected; the advisory and its fix were about the token." how-type: the fix must understand
   which inputs feed the digest and re-source them without breaking the identifier.
3. **T3 injected sibling (shape trap)** — the boot/usage payload carries the configured Redis
   connection URL verbatim next to the feature flags; a URL commonly embeds a password, so a
   name-based "drop the X_secret field" fix misses it. Producer is appProperties, untouched by the
   published fix.
   where: telemetry/telemetry.go appProperties (injected `redis-url` property).
   dismiss: "it is deployment context (a host/endpoint), not a secret field."
   how-type: the credential is part of a larger value.
4. **T4 injected sibling (second route for the consent clause; defaults/merge)** — a
   `[telemetry]` section in the TOML config file with `enabled = true` and no token authenticates
   with a shared token built into the product (config.TelemetryOptions), merged into the telemetry
   config in WithTelemetry. Reachable from the real CLI via `--config-path`. Published fix never
   touches config/config.go or cli/runner_options.go.
   dismiss: "the operator explicitly enabled telemetry in their config, so consent is given; the
   token is just plumbing."

Different dismissals: T1 supported-token-less sending; T2 harmless-hash/out-of-scope; T3 not-a-
secret-field; T4 explicit-consent.

## Sites / routes / input shapes the security tests cover

- default binary start with no token, no config (T1) — no request.
- config file `[telemetry] enabled` without token (T4) — no request.
- secret supplied through an ANYCABLE* env value (T2) — payload invariant.
- secret supplied through a CLI argument value (T2) — payload invariant.
- secret supplied through the config file's secret line (T2) — payload invariant.
- password embedded in a configured Redis URL (T3 and T2) — payload invariant + raw absence.

Invariance test shape: three real binary runs in one test — A and A' with identical configuration,
B with only the secret value changed. Every JSON field that is stable across A/A' must be equal in
B. (distinct_id is random per run and is therefore skipped automatically; a per-run random
replacement identifier would also be skipped, which is acceptable: it does not derive from the
secret.)

## Coupled must-keep-working behaviour (functional)

- With a deployment-supplied token, the boot event is delivered with its documented properties,
  custom props and the token as the Authorization header, and the server starts and serves /health.
- ANYCABLE_DISABLE_TELEMETRY=true still silences telemetry even with a token.
- A token supplied through the config file still enables telemetry (over-broad removal of the
  config section must fail).
- Telemetry still reports a configuration that has a secret set (an over-broad "never send if a
  secret exists" must fail).

## Sibling candidates found (full list) and why the picks won

1. cli/runner_options.go:189 — second opt-in/opt-out route with its own Config default (screener
   O8b #1). PICKED as T4: config-file `[telemetry]` section with a built-in fallback token. It is
   reachable from the CLI, sits in config defaults/merge (how-type), and its dismissal (explicit
   config consent) is distinct. A CLI flag variant was rejected: setting a flag still looks like
   consent, but a flag default overlaps the reported default and is caught by the base test.
   A preset variant was rejected: presets load after options, so the merge would have had to sit
   next to the published fix's lines in cli/cli.go.
2. telemetry/telemetry.go appProperties (screener O8b #2) — raw config value next to the feature
   flags. PICKED as T3 (Redis URL, credential inside a larger value). It is a shape trap, not just
   a second field, and its dismissal ("a host, not a secret") differs from the hash dismissals.
3. telemetry/telemetry.go appProperties — debug-only dump of the effective config TOML. Rejected:
   same site as #2, same raw-value shape, and its "debug only" dismissal is a weaker judgement
   trap; it would not add a distinct mechanism.
4. telemetry/telemetry.go NewTracker — distinct_id made stable by deriving it from the app secret.
   Rejected: NewTracker is touched by the published fix and the shape duplicates T2 (secret ->
   digest sent in the payload).
5. telemetry/telemetry.go Send — extra header/query carrying the config. Rejected: contrived for a
   maintainer and the same raw-value shape as #2.
6. cmd/embedded-cable/main.go — a second binary with its own telemetry option and built-in token.
   Rejected: a sample binary, hard to run deterministically offline (fixed :8080) and a pure
   where-type extra.
7. config/presets.go — a preset injecting a telemetry token. Rejected on ordering (see #1).
8. telemetry/config.go — a second build-time variable. Rejected: same file as the reported landing
   point, so the report already leads there.
9. metrics/, diagnostics/ — no telemetry sink; not reachable under the property.

## Verified (what was run)

- The pinned binary reproduces the default egress: POST to ANYCABLE_TELEMETRY_URL with
  `Authorization: secret` and a `cluster-fingerprint` computed from the environment (checked with a
  local capture server; secret changes change the fingerprint).
- `go build ./...`, `go test ./cli ./config` pass at the pinned commit.
- The telemetry package's own TestTracking encodes the vulnerable default (it never sets a token);
  after the fix it only passes with the upstream test edit, so it is NOT used as a grading test.
  Our functional suite carries an adapted copy that sets a token.

## Check patches, verified locally against the final suite (2026-10-24)

Each patch was applied to a clean pinned+injected tree and the whole hidden suite was run:

- sf_t1_default — security 2 fail (stock start, config opt-in), functional all pass.
- sf_t2_fingerprint — security 4 fail (all secret-invariance routes), functional all pass.
- sf_t3_embedded_credential — security 1 fail (embedded credential), functional all pass.
- sf_t4_config_route — security 1 fail (config opt-in), functional all pass.
- ff_no_telemetry — security 4 fail (no event at all), functional 2 fail (token routes dead).
- ff_config_route_removed — security all pass, functional 1 fail (config token route removed).
- pass_hardening — all pass.
- pass_alt_drop_fingerprint — all pass.
- Base (pinned+injected, no patch) — security 6/6 fail, functional 5/5 pass.
- Oracle (solution/fix.patch) — security 6/6 pass, functional 5/5 pass.

The base, oracle and sf_t2 rows were re-run with the final suite after the timing windows were
widened (15 s to observe an expected event, 3 s of silence after a start); the other rows used the
same test logic with the earlier windows, with the same outcomes.

## Outside the advisory's protection (one line each, not built on)

- `anycableCLIArgs` sorted `os.Args[1:]` in place, mutating the process-global argument slice; the reference fix no longer reads argument values, which removes the mutation as a side effect, but no test depends on it.
- The published commit also bundled an unrelated `metrics/metrics.go` change (`defer close(serverErr)`); it is not part of the task.
- A disabled tracker returned for an empty token has no logger/client; the reference fix makes `Collect`/`Send` inert, but calling `Shutdown` on it would still panic (same as upstream) and no test does.

## Gate results (2026-10-24)

- static: PASSED (after the blind-pass declaration; FAIRNESS.md and checks/blind.patch are written by the pipeline's later steps).
- nop: PASSED — 6/6 security tests fail on the pinned+injected tree, 5/5 functional pass.
- oracle: PASSED — 3 identical trials at reward 1.0 (6/6 security, 5/5 functional each).
- patches: PASSED 8/8 as declared: sf_t1_default 0.6667 (stock start + config opt-in fail), sf_t2_fingerprint 0.3333 (all four invariance tests fail), sf_t3_embedded_credential 0.8333, sf_t4_config_route 0.8333, ff_no_telemetry 0.0 (functional fail), ff_config_route_removed 0.0 (functional fail), pass_hardening 1.0, pass_alt_drop_fingerprint 1.0.

Two infrastructure flakes were retried and not worked around in the task: the shared host Docker daemon
deadlocked under load during the first attempts (the operator restarted it; private dockers were then
abandoned on instruction), and one check trial was rejected by Harbor's allowlist egress probe and
passed on the stage retry.

## Not verified / guesses

- Whether models will miss enough; no trials are run by the builder.
- `present_in_latest` for the fingerprint route: not checked against current upstream.
- repo_mb not measured.
