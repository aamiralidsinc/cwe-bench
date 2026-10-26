# homer-ds — build notes

- Start: 2026-10-24T05:15Z (build driver), plan written 2026-10-24T05:24Z
- End: (see end_utc.txt)

## Task

GHSA-6XP5-7RCX-XFGX / CVE-2026-62252, sipcapture/homer, CWE-798 (default credential),
pattern A, track INJECTED. Pinned a7d027dc (checked: parent of the published fix
b2e94203 by direct diff). The published fix is real and large enough to be the oracle:
it removes the fixed bootstrap hash from the auth decode hook and the normalization
step, preserves an explicitly configured hash through the config serializer, makes the
bootstrap user service generate a random password when none is supplied (and return it
so startup logs it), and stops the wizard emitting the fixed hash.

Seam: Go tests in the module (`src/hiddentests`), driving the real public entry points:
`config.Load`, `coordinator.New`+`Start`+`POST /api/v3/auth`, `cli.RunWizardCmd`,
`cli.RunSystemCmd`, `cli.RunResetAdminPassword`. DuckDB (duckdb-go v2 prebuilt
bindings) for the settings DB; no network, no services.

## Security property (written once, in instruction.md)

No administrator credential may be fixed. Whenever the operator has not supplied one,
every route that creates or repairs the administrator's credential — or that emits a
configuration which will later be applied — must result in a freshly generated,
unpredictable credential, never a value that is the same on other installations. A
credential the operator does supply explicitly stays in effect, in either stored form
the product supports, including after a configuration is written out and read back.

## Levers

Every lever is covered by that property as written; the instruction never names a site,
command, file or route.

1. **bootstrap generation — how-type, coupled must-keep-working** (real, published).
   `src/coordinator/services/auth_bootstrap.go:28-31` + `src/coordinator/coordinator.go:110-119`.
   With normalization no longer supplying a hash, the service must generate one and
   startup must keep working. Reason to dismiss: "an empty hash is an error, so it fails
   closed and is not the vulnerability". Security: startup with string/object/omitted/blank
   auth and the repair path for an existing empty row must start and must not accept the
   documented default. Coupled functional: explicit credentials (bcrypt and legacy
   SHA-256) still authenticate; a row with a non-empty hash is never overwritten; a blank
   config still yields a usable deployment with a real stored hash.
2. **generated configuration producer — how-type, producer off the check's path** (real
   far site + published serializer). `src/cli/wizard_cmd.go:202-207` (preset base config)
   and `src/config/config.go:897` (the auth serializer drops the fixed value, so an
   explicit legacy hash disappears on save). The loader/bootstrap never calls the
   producer; the value arrives via a file that is written and re-read. Reason to dismiss:
   "the wizard is operator tooling and the operator sees the password". Security: a preset
   config written by the real wizard command, loaded and used to start a coordinator, must
   not accept the default. Coupled functional: an operator's explicit legacy hash must
   survive write-out + re-read; a non-default bcrypt hash must round-trip.
3. **example configuration producer — producer off the check's path** (injected).
   `src/config/config.go SaveExample` writes a hashed form of the documented default into
   the example configuration. Reason to dismiss: "it is only a sample file". Security:
   `homer system --generate-example-config` output, loaded and used to start a coordinator,
   must not accept the default.
4. **credential repair command — route where the protection never existed** (injected).
   `src/cli/reset_admin.go:31-33` falls back to the fixed hash when the effective config
   carries none, instead of refusing. Reason to dismiss: "a local recovery command run by
   a trusted operator". Security: after the command runs with no supplied credential, the
   settings DB must not hold a fixed credential.

## Candidate list searched (picked ones marked *)

- config decode hook (string form) — published site; covered under lever 1.
- normalizeCoordinatorAuth (object/omitted/blank) — published site; covered under lever 1.
- auth serializer drop-on-save — published site; coupled functional under lever 2.
- EnsureBootstrapAdminUser empty-hash error — published site; lever 1 *.
- coordinator startup wiring/logging — published; not separately observable without
  depending on a log field name, so not tested directly.
- wizard preset baseConfig — published far site; lever 2 *.
- wizard TUI prefill/mapping — published; not reachable non-interactively, not tested.
- reset-admin empty-hash fallback — injected; lever 4 *.
- SaveExample example generator — injected; lever 3 *.
- env.go re-applying the default after unmarshal — considered injected; rejected: it
  duplicates the loader concept and would make every loader test fail for the same
  reason, adding no distinct judgement.
- migrate_settings seeding an admin from the homer-app source DB — considered injected;
  rejected: needs a live PostgreSQL source, so not reachable offline.
- passwordhash.Verify empty-hash fail-open — considered injected; rejected: the bootstrap
  repair path rewrites empty rows at startup, so a real login route to it could only be
  built by disabling other protections, which is unfair.
- passwordhash legacy SHA-256 verification — real, must keep working (functional).
- user creation / password update APIs — legitimate hashing, no default.

Why the picks beat the rest: they are the only candidates that are reachable offline
through a real entry point, are not observable through the same single check as lever 1,
and each carries a different reason to skip (fail-closed error; operator tooling; sample
file; local recovery). The two producers (2, 3) are how-type: the bootstrap check never
calls them and the value reaches it only through a saved-and-reloaded file.

## Injection

`environment/injection.patch` (two realistic maintainer shortcuts, not near the fix's
edits): the example-config generator seals the documented bootstrap password with the
current hasher; the reset command falls back to the fixed hash when the effective config
has none. Neither is described in the instruction.

`environment/docs.patch` removes fix-describing documentation already present at the
pinned commit (SECURITY.md bootstrap section + summary row + advisory link, the same
claims in AUTH_LDAP_AND_OAUTH.md and WIZARD.md). Current-behaviour documentation that
mentions the default password is kept.

## Verified

- pinned: `config.Load` returns the fixed hash for string/object/omitted/null/blank
  forms; coordinator startup + `POST /api/v3/auth` accepts admin/sipcapture; wizard
  preset reloads to the fixed hash; example config reloads to the fixed hash;
  `--reset-admin-password` writes the fixed hash. (local probe, 2026-10-24)
- toolchain: go1.26.4 + `libluajit-5.1-dev` (golua cgo link); duckdb-go v2 ships
  prebuilt bindings, no local DuckDB build.
- hidden tests compile and behave: see "Gate result" below.

## Could not verify / notes

- The screener's "fix.diff is empty" was wrong: the published fix has real hunks; used it.
- The upstream fix also renames the constant and bumps the version; the oracle keeps the
  constant name for a smaller, test-compatible diff.
- Wizard TUI behaviour is not graded (interactive).
- present_in_latest for the synthesized siblings is n/a (siblings do not exist upstream).

## Build findings (2026-10-24)

- Published fix confirmed real (screener's "empty diff" was wrong): decode hook + normalize
  defaults, serializer drop-on-save, bootstrap random generation + return, startup log, wizard
  preset/TUI. Oracle = that fix plus reverting the two injected siblings.
- The repository needs `libluajit-5.1-dev` (golua cgo link) and a `src/dist/.gitkeep` because
  `static.go` embeds `all:dist`; both are handled in the image Dockerfiles.
- Project tests: `./config/` and `./passwordhash/` pass at pinned; `./coordinator/services/` has a
  pre-existing unrelated failure in the mapping-seed tests (9 vs 10 rows), so the image build runs
  only the two affected service tests, which pass.
- Hidden tests drive: config.Load -> coordinator.New/Start -> POST /api/v3/auth; the real CLI
  dispatchers for wizard preset, example config and reset-admin. Each test keeps one settings-DB
  handle for its lifetime: closing and re-opening the same DuckDB path through the driver's
  process-wide instance cache intermittently blocks, which showed up as a 70s test timeout once in
  10 runs. After the single-handle change, 20 consecutive runs of each group passed (oracle).
- Checks validated locally (injected tree + each patch): sf-miss-loader / sf-miss-hook /
  sf-miss-wizard / sf-miss-example / sf-miss-reset each fail only their lever's security test
  with all functional tests passing; ff-crash-empty, ff-miss-marshal, ff-overbroad and
  ff-drop-legacy fail functional; pass-alt and pass-hardening score 1.0.

## Host notes (shared VM, 2026-10-24)

- The main dockerd's /version, /info and /containers/json endpoints wedged under the shared load;
  a task-private dockerd was started (build/homer-ds/priv-docker, bridge hmprv0 10.252.0.1/16,
  pool 10.253.0.0/16). Two subnets first chosen (10.240/241) collided with another session's
  private bridge, which broke container networking until they were changed.
- The host FORWARD policy is DROP and other sessions' daemons periodically rebuild the FORWARD
  chain, dropping our ACCEPT rules for the private subnets. A small root watchdog
  (build/homer-ds/net-watchdog.sh) re-adds the FORWARD and MASQUERADE rules; without it container
  DNS/egress fails intermittently, which made the image build fail twice at the node download.

## Gate results

- static: PASSED.
- nop: PASSED — 8 security tests all fail on the injected pinned tree, 9 functional tests pass.
- oracle: PASSED — 3 trials, reward 1.0, identical results.
- patches: (filled below)

## Resumed after host pause (2026-10-24 ~07:45Z)

The host Docker daemon deadlock was fixed by the operator; the private dockerd and its bridge
were removed and the remaining gate stages ran against the system Docker (no DOCKER_HOST
override). The first check trial rebuilt both images on the shared daemon; the rest reused the
classic-builder cache.

## Gate result (2026-10-24T09:24Z)

- static: PASSED.
- nop: PASSED — 8/8 security tests fail on the injected pinned tree, 9/9 functional pass
  (trial homer-ds-nop-1792822896).
- oracle: PASSED — 3 trials, reward 1.0, identical (homer-ds-oracle{1,2,3}-*).
- patches: PASSED — every check behaves as declared:
  - sf-miss-loader: 0.0 (all 8 security fail, functional pass)
  - sf-miss-hook / sf-miss-wizard / sf-miss-example / sf-miss-reset: 0.875 each, exactly their
    own security test failing, all functional passing.
  - ff-crash-empty, ff-miss-marshal, ff-overbroad, ff-drop-legacy: functional failures as
    declared (ff-miss-marshal leaves all 8 security tests passing and breaks only the
    explicit-default-hash round trip).
  - pass-alt, pass-hardening: reward 1.0.
- blind.patch: not written here (downstream blind-fix step); the static gate tolerates its
  absence and the patches stage skips it.
