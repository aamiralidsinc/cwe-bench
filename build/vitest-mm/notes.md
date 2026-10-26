# vitest-mm — build notes

- Start (UTC): 2026-10-18T19:12Z (prompt handed over) / 19:30Z (plan written)
- End (UTC):   2026-10-18T20:40Z (deliverables written; gate follows)

## Advisory
GHSA-5XRQ-8626-4RWP / CVE-2026-47429, vitest-dev/vitest. Missing authorization on the
network-reachable test-runner control API plus path confinement (CWE-862 / CWE-22).
Pinned (vulnerable) commit `76c4397b58618b6b430b0800487995c77bb6dad7` — parent of published
fix `20e00ef7808de6d330c5e2fda530f686e08f1c8d`. (`af88b1f5` is a v3 backport; ignored.)
Track: injected. Pattern: A+B.

## Why this build exists
`vitest-api-fs-authz-inj` (same advisory, previous build) scored MiMo 1.0 on 2/2 finished
runs and DeepSeek 0.625 on 3/3. MiMo found and gated every write/exec handler the previous
tests exercised (UI handlers, browser file commands, both injected siblings) and even gated
browser-RPC snapshot writers that were not tested. This build must therefore be harder on
scope and on the second half of the advisory — without naming anything the solver may not see.

## Two invariants (the report will state these)
1. **Authorization (CWE-862).** When the control server is reachable from the network, no
   request from a client may create, modify or delete any file, and no request may cause test
   code to run — whichever operation, whichever interface, whichever target. Refusal is a
   clean client error or a silent no-op; the server keeps running and disk is unchanged.
2. **Confinement (CWE-22).** No request from a client may read or write a file outside the
   project's files — whichever operation, whichever interface, and **whatever file-serving
   settings the project has**. (This clause is the fairness hook for the strict=false bypass.)

Coupled must-keep-working: reads keep working; local save/run/snapshot/browser file ops keep
working exactly as today; a file the server never registered is still rejected as before.

## Levers (one line each)

| id | pattern | shape | where | reason to dismiss |
|----|---------|-------|-------|-------------------|
| A1 | A (reported) | missing write/exec authz on the control server | `packages/vitest/src/api/setup.ts` — save / run / re-run / snapshot-update handlers | n/a (this is the reported site) |
| A2 | A (far site, 2nd implementation) | same missing write authz on the browser-mode file commands | `packages/browser/src/node/commands/fs.ts` writeFile/removeFile | "browser-test server; its writes are the user's own test code; gating looks like breaking browser tests" |
| A3 | A (producer / defaults-merge) | host spellings + api number-vs-object + browser.api inheritance | `packages/vitest/src/node/config/resolveConfig.ts` `resolveApiServerConfig` | "config plumbing, not a request handler" — enforced only by input-shape variants |
| B1 | B (uncovered route) | attachment read accepts any path when the project widens web-server file serving | `packages/browser/src/node/plugin.ts` HTTP `/__vitest_attachment__` | "read-only helper copied from the UI package; the fix is about write/exec" |
| B2 | B (confinement, write form) | a write command accepts a path outside the project when serving is widened | `packages/browser/src/node/commands/fs.ts` writeFile path | "the serving check is the documented Vite API; migrating it is the fix" — the old AND the new Vite helper both return true when `server.fs.strict` is false |
| S1 | injected sibling | extra browser command `exportArtifact(path, data)` with only the pre-fix file check | **new file** `packages/browser/src/node/commands/artifacts.ts` + registration in `commands/index.ts` | "test-evidence export helper, not the file API the report names" |
| S2 | injected sibling | HTTP write companion on the attachment endpoint | `packages/ui/node/index.ts` `POST /__vitest_attachment__` | "the attachment endpoint is the UI's read-back of test evidence; a save companion is an upload helper, not the control API" |

**Producer (A3) is not a standalone test** — it cannot fail `nop` (pinned code has no flags).
It is enforced by shape variants inside the A1/A2/S* tests: host `127.0.0.1` and unset host
must keep working, host `0.0.0.0` and any other host must refuse, `api` given as a bare port
number must behave as local, and a browser project's api must inherit the root's binding.

## Input shapes covered (not extra levers)
- host: unset / `localhost` / `127.0.0.1` → local; `0.0.0.0` / other → exposed
- `api` given as a number vs as an object
- a browser project inheriting the root `api` binding vs its own
- write form vs read form of the confinement invariant
- update-snapshot with and without a named file

## Injected siblings — realism notes
- **S1** `exportArtifact`: commands in `@vitest/browser` are small functions registered
  beside one another (`commands/index.ts`); screenshots already live in their own module, so
  an evidence/artifact export in its own module is the natural next step. It copies the
  pre-fix `writeFile` shape exactly (resolve under root, file check, mkdir, write).
  Published fix never touches `commands/artifacts.ts` or `commands/index.ts`.
- **S2** HTTP write on `/__vitest_attachment__`: the UI node package already has that path as
  a GET read-back of test attachments; a maintainer adding "save an attachment" adds the
  matching POST to the same middleware. Published fix never touches `packages/ui/node`.
  Dismiss reason is strong because the report speaks only of the control API's write/exec
  operations, and this is an HTTP helper next to a read.

## Sites / routes / shapes the security tests will cover
1. UI control API: overwrite a registered test file (A1)
2. UI control API: start a run of named files (A1)
3. UI control API: run a single task (A1)
4. UI control API: snapshot update, with and without a named file (A1)
5. browser file command: create a file (A2)
6. browser file command: delete a file (A2)
7. browser HTTP attachment GET naming a file outside the project, under widened serving (B1)
8. browser file command: create a file outside the project, under widened serving (B2)
9. injected artifact export: create a file (S1 authz)
10. injected artifact export: create a file outside the project (S1 confinement)
11. injected UI HTTP save: write a file (S2 authz)
12. injected UI HTTP save: write a file outside the project (S2 confinement)

## Coupled must-keep-working (functional)
- UI: local save / run / run-one / snapshot-update still work; unregistered save still
  rejected; reading a registered test file still works while exposed.
- browser commands: local create/delete work; reading a file still works while exposed.
- confinement positive control: reading/writing a file **inside** the project still works,
  including under widened serving.
- S1 exportArtifact and S2 HTTP save still work locally.
- producer shapes: host `127.0.0.1` and unset host and `api` as a bare number still allow
  local writes; a browser project still inherits the root binding.

## Test seams (verified in the earlier build of this advisory, reused)
- UI control API: `createVitest('test', {api:{port:0,host}, watch:true}, {})` then a minimal
  birpc-over-WebSocket client with the server's own token (same as the product's UI client).
  `rerunFiles` / `rerunTask` / `updateSnapshot` are monkey-patched on the real ctx to record
  calls; `state.filesMap` is seeded with a real temp file so the registered-file gate passes.
- browser file commands: exported functions called with the browser project the runner
  resolves (`createVitest` + inline browser project (preview provider) + `_initBrowserServers()`).
  No browser is launched. Sources loaded as TS via alias (browser dist does not re-export them).
- browser HTTP attachment: the same browser project's vite server is already listening; the
  test issues a real HTTP GET with the product's token.
- UI HTTP save (S2): `ui: true` so the UI plugin's middleware is mounted; real HTTP POST.
- Widened serving: `server.fs.strict = false` (a documented Vite option) in a small config
  file in the project root, and the browser project `extends` that file. `extends` is required:
  inline project options do not carry a `configFile`, and `createBrowserServer` rebuilds its
  vite with `server: {hmr,watch}` which drops an inline `server.fs`. Verified: root, project
  and browser vites all report `fs.strict === false`, and every planned hole then reproduces.
- Producer shapes are driven by the host/api arguments to `createVitest` (unset, `127.0.0.1`,
  `0.0.0.0`, bare port number) and by a browser project that does vs does not set its own
  `browser.api`.

## Wrong-fix / patch-check plan
- `base_only` — gates only the reported UI handlers → security_fail
- `miss_far` — oracle minus the browser-command write gate → security_fail
- `miss_conf` — oracle keeps authz but keeps the weak serving check (published fix alone) → security_fail
- `miss_s1` / `miss_s2` — oracle minus that sibling's gate → security_fail
- `write_only` — gates writes but not the run/re-run (exec) half → security_fail
- `localhost_blocked` — refuse-all, even local → functional_fail
- `reads_blocked` — over-broad: the write gate is also placed on reads → functional_fail
- `hardening` — oracle + a stricter confinement helper in the module the security tests import → pass
- `alt_fix` — a second valid design (host-based, no config flags) → pass

## What I will verify
- flaw reproduces at pinned+inject through the real entry point (UI WS + browser commands +
  browser HTTP attachment + UI HTTP save)
- nop: every security test fails, every functional passes
- oracle: reward 1.0, twice, identical
- every declared check patch behaves as declared
- no leak terms in instruction.md; project's own offline config-resolution behaviour reproduced

## Verified (local, work repo)
- Every planned hole reproduced at pinned+inject through the real seam (12 security tests fail).
- Local nop: security 12/12 fail, functional 16/16 pass.
- Local oracle (host-based design, no allowWrite/allowExec names): security 12/12 pass, functional 16/16 pass.
- instruction.md: 522 words, leak scan clean (no advisory id, no commit sha, no fix-patch filenames, no leak_terms).
- All ten check patches apply cleanly on pinned+inject.

## Gate
- static: PASS except the two post-build items (blind patch, FAIRNESS.md).
- nop: PASS (12 security fail, 16 functional pass).
- oracle: PASS (3 runs under strict_gate, identical).
- patches: (in progress) clean trials so far match their declarations —
  `base_only` 0.3333, `miss_far` 0.8333, `miss_conf` 0.6667, all `security_fail`.
  Remaining checks blocked by an intermittent Harbor/infrastructure flake
  (egress-control kernel probe failing under VM load → `network_mode='allowlist'
  is not supported by EnvironmentType.DOCKER`), not by a check-expectation failure.
- Image-build fix along the way: the injected `assertFileAccess` export needed an explicit return type for `--isolatedDeclarations`; inject.patch updated, fix.patch and all checks regenerated.
- Harness fix along the way: the WS client now connects to the address the live server actually bound (IPv6 `::1` otherwise refused `127.0.0.1`).

## What I will not do
- no trials, no target models, no `blind` patch, no `FAIRNESS.md` (post-build step writes those)
- no network at test time; no GPU/GUI/Playwright browser launch
- no browser-RPC WebSocket handlers as tested levers (they need a live session id + provider
  handshake; recorded in the manifest as known-uncaught). The published fix gates them; the
  invariants here are already covered at the UI API and the command API.

## Out of scope (noted, not built)
- `packages/mocker` registerMock redirect path join (different transport, module redirection)
- `packages/vitest/src/node/test-run.ts` artifact copy source (reached from the browser RPC,
  which this task does not drive)
- `sendCdpEvent` / `trackCdpEvent` (provider-specific CDP, not a file or test-run operation)
