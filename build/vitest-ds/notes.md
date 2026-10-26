# vitest-ds — build notes

- Start (UTC): 2026-10-18T19:08:03Z
- End (UTC):   2026-10-18T21:56Z

## Advisory
GHSA-5XRQ-8626-4RWP / CVE-2026-47429, vitest-dev/vitest. Missing authorization on the
network-reachable test-runner control API (write/exec) plus path confinement (CWE-862 / CWE-22).
Pinned (vulnerable) commit 76c4397b58618b6b430b0800487995c77bb6dad7 — verified to be the parent
of the published fix 20e00ef7808de6d330c5e2fda530f686e08f1c8d. Track: injected. Pattern: A+B as
assigned; realized as A (reported site + far second-implementation sites) + two injected siblings.

This build started from the previously verified artifact for the same candidate (built earlier
today as vitest-api-fs-authz-inj). I re-verified the pinned tree, the flaw and the oracle locally,
then reworked the browser-side harness and added coverage; every gate stage is run fresh for
this slug.

## Levers (one line each)
- BASE (A, reported): UI control-server write/exec RPC handlers — packages/vitest/src/api/setup.ts saveTestFile (write) + rerun/rerunTask/updateSnapshot (exec). Dismiss: n/a (reported).
- A-FAR (A, far site, second implementation): browser-mode file commands writeFile/removeFile — packages/browser/src/node/commands/fs.ts (different package, real browser-API WebSocket). Dismiss: "separate browser-test server, writes are the user's own test code, gating looks like breaking browser tests."
- A-SNAP (A, far site): browser-mode RPC snapshot handlers saveSnapshotFile/removeSnapshotFile — packages/browser/src/node/rpc.ts. Dismiss: "snapshot files are test artifacts produced by the run, not source files."
- S-CMD (injected sibling): extra browser file command appendFile with the pre-fix pattern — fs.ts + commands/index.ts. Dismiss: "convenience append helper, not the create/delete pair named."
- S-UI (injected sibling): extra UI write handler saveSnapshotFile gated only by registered-file membership — setup.ts + api/types.ts. Dismiss: "snapshot editor action on an already-registered file."
- PATH (B, advisory CWE-22 half): browser write commands escaped the project root (relative and absolute shapes) when the project's file-serving restriction is relaxed — packages/browser/src/node/commands/fs.ts assertFileAccess. Dismiss: "the code already runs Vite's file-serving check before the write, so the path looks confined."
- Producer (enforced, not a standalone test): resolveApiServerConfig defaults (localhost/unset -> allow, network host -> deny, browser.api inherits) is forced by the exposed-refuses + localhost-works test pair.

## Fairness revision (important)
The earlier build's browser tests called the command functions directly. Reviewing the earlier
trial patches showed a model gating the real browser RPC dispatcher (`triggerCommand`) — a
legitimate fix — which those tests rejected. The tests now create a real browser project, add a
session through the runner's own registry, connect the product's browser-API WebSocket as the
orchestrator does, and request commands through the real `triggerCommand` handler and snapshots
through the real `saveSnapshotFile` / `removeSnapshotFile` handlers. A new `rpc_only.patch`
alternative, gating only the RPC layer, scores 1.0, and the blind patch (which missed only the
injected UI handler) is recorded honestly. All tests remain host-driven and offline: the preview
provider starts the real servers but launches no browser.

## What I verified (locally, offline, repo's own toolchain)
- The flaw reproduces through the real entry points at pinned+inject: the live UI API WebSocket
  overwrites a registered test file and starts runs; the live browser-API WebSocket writes,
  appends and removes files and writes/removes snapshot files with host 0.0.0.0; and with the
  project's file-serving restriction relaxed, a local client's write/remove through the browser
  command API lands outside the project root.
- nop (pinned+inject): security 0/13, functional 11/11.
- oracle (inject+fix.patch): security 13/13, functional 11/11, reward 1.0 (three strict-gate Docker runs, identical).
- All 16 declared check patches verified locally with the fair harness. Each single-lever
  security_fail patch fails only its own lever (miss_far/miss_snap/write_only 2 each;
  miss_scmd/miss_sui/miss_update 1 each) with functional 11/11; miss_path fails the 3
  path tests (10/13, 0.7692); base_only fails 9 (4/13); blind_r1 fails 4 (9/13).
  localhost_blocked (functional 3/11), reads_blocked (10/11), ui_reads_blocked (10/11) fail
  functional; hardening / alt_fix / host_fix / rpc_only pass 1.0 (13/13, 11/11).
- inject.patch applies cleanly to the pinned commit; fix.patch applies cleanly to pinned+inject
  with `patch -p1`. fix.patch excludes the unrelated packages/utils/src/source-map.ts noise from
  the upstream commit and adds explicit root containment for the write commands (CWE-22 half).
- Docker gate: static clean except the two deliberately-post-build items (blind pass patch and
  FAIRNESS.md); nop PASSED on the final artifact (security 0/13, functional 11/11); oracle PASSED
  (3 strict runs, each security 13/13, functional 11/11, reward 1.0, identical results).
- Docker gate, patches stage: NOT completed. The shared VM was running 18-19 concurrent gate
  stages, each executing `docker network prune -f`; trials were repeatedly destroyed between
  network creation and container start (RuntimeError: "network ... not found"; one "Harbor
  produced no trial"). A local `docker compose` retry shim (PATH-only, our process tree; no gate
  or task change) removed the network race, and the shimmed run validated base_only (4/13 sec,
  11/11 fun), miss_far (11/13), miss_path (10/13), miss_snap (11/13), miss_scmd (12/13),
  miss_sui (12/13) before Harbor itself failed to start the write_only trial. Earlier aborted
  Docker runs also validated write_only (11/13) and localhost_blocked (13/13 sec, 3/11 fun).
  Every one of the 16 check patches was verified locally with the final suite (see above);
  reads_blocked / hardening / alt_fix / miss_update / ui_reads_blocked / host_fix / blind_r1 /
  rpc_only have local evidence only. This is an infrastructure cut, not a check failure.
- The project's own config-resolution suite (test/config/test/override.test.ts) passes on the
  pinned+injected tree: 23/23.
- Verifier determinism: the UI harness connects to the server's actually-bound port (Vite falls
  back to the next port while a previous test releases the default), registers its test file
  inside the project root (so a solver applying the root invariant to UI handlers is not
  penalised), and test.sh rebuilds the whole workspace because a fix may live in a shared package
  (~70 s in the 2-CPU container).

## What I could not / did not do
- Pattern-B uncovered routes were investigated and DISMISSED (register rows added): (1) the UI
  source-viewer read handlers' deprecated serving check is a NO-OP to "fix" in this tree — in
  vite 7.1.5 the stricter loading check also returns true when server.fs.strict=false, so the
  published fix's read-path switch does not confine reads here; read-only, not fix-closable.
  (2) browser onTaskArtifactRecord attachments have no deterministic offline disk-effect oracle.
- Project browser/UI Playwright e2e specs were deliberately not used (GUI/flaky/offline). Their
  config-resolution coverage is reproduced offline via createVitest and the real RPC servers.
- Docker gate stages (static/nop/oracle/patches) are run by builder/gate.py on the shared VM.
- FAIRNESS.md and the blind pass-patch are intentionally left for the post-build step.

## Fairness note
Everything the tests require is reachable from instruction.md + code: the instruction states the
invariant generically ("no request ... may create, modify, or delete any file ... or cause test
code to run ... whichever operation, through whichever interface, and whichever target") which
covers the far sites and both injected siblings without naming them. The two injected siblings sit
beside real handlers with the same pre-fix shape. The tests drive the real network entry points,
so a fix at any layer between the socket and the sink passes. Residual risk: the published fix
introduces user-visible write/exec options and the local-vs-network default rule; the instruction
conveys this as "reachable from the network -> refused, local -> works" without naming fields.

## Sibling-injection upgrade (2026-10-20, BETTER-PATTERNS §2–§8)

Instruction-only + tests/checks/metadata upgrade; no repo code, no Dockerfile, no fixture change, so
the prebuilt image was reused and NOT rebuilt.

- Instruction: replaced the route checklist (the token-bearing page, "browser-based UI and the
  browser-mode test driver", the exact overwrite example, "one of the project's test files", the
  snapshot and browser-test operations in the keep-working clause, the relaxed-file-serving
  configuration stage) with ONE general property over the protected outcome: while the server is
  network-reachable no request may create/modify/delete a file or execute project code; no request
  may change a file outside the project root at any binding; reads keep working; local writes/exec
  keep working; unregistered files stay rejected. No route, operation, channel or stage is named.
- Levers: unchanged where-type ones (BASE, A-FAR, A-SNAP, S-CMD, S-UI) plus the existing how-type
  ones (the exposure producer in config resolution and the root-confinement route where protection
  never existed). Added one explicit how-type lever ART (M4/M6, real upstream code, no repo change):
  a client records a test artifact; the runner's own `recordArtifact`/`resolveTestAttachment`
  producer copies each named attachment into the attachments directory. The RPC handler never
  consults write authorization; the published fix strips attachments when writes are disabled, so
  the oracle already closed it — it was listed as known-uncaught and is now covered.
- Coverage: added `security/browser_commands.test.ts::recording an artifact with an attachment does
  not create a file`, `...recording an annotation with an attachment does not create a file`, and
  the coupled positive control `functional/browser_commands.test.ts::records a test artifact
  attachment when writing is allowed`. The harness gained `seedTest`, which registers one test
  entity through the runner's own `state.collectFiles` (the same call the product makes while
  collecting), so the real browser-API handler is driven end to end.
- Checks: `checks/miss_artifact.patch` (the oracle minus the artifact strip) is the new
  security_fail check. `host_fix.patch` and `rpc_only.patch` were regenerated with an
  `assertApiServerNotExposed(vite, 'onTaskArtifactRecord')` line so both independent correct fixes
  still score 1.0. `blind_r1.patch` now misses 2 security tests (recorded honestly); base_only,
  localhost_blocked, reads_blocked, ui_reads_blocked keep their expectations.
- Verified in the prebuilt image (scratch container, tests copied as test.sh does): pinned code =
  security 0/15, functional 12/12 (the 2 new security tests fail because the attachment file is
  created, including the `note-<hash>.txt` annotation shape); oracle = 15/15 + 12/12, reward 1.0;
  miss_artifact = 13/15 security (only the 2 new tests fail) and 12/12 functional; host_fix and
  rpc_only = 15/15 + 12/12, reward 1.0. Static leak scan is clean; the only static failure left is
  the pipeline-supplied blind pass patch, which is wired separately.

## Frontier-1.4 hardening (2026-10-21)

The v3 task was solved 3/3 by the target model, so three new fair levers were added and the
delivery was converted from the shared-mode `/app` format to Frontier 1.4.

New levers (each covered by the existing general property, no route named to the solver):
- INHERIT (MERGED/DEFAULTS · HOW-type): the browser-mode API server's write permission is
  defaulted from the runner's own api settings (`resolveApiServerConfig(..., parentApi)`), so an
  exposed browser server inherits `allowWrite: true` from a locally bound runner API. Reason to
  dismiss: inheritance is how the configuration works, and the parent server is trusted/local.
  Security test: exposed browser API + local runner API, `writeFile` must not take effect.
  Coupled: reads still work in that configuration; ordinary local writes keep working.
- LINK (resolved-location input shape · HOW-type): containment compares the spelled path. A
  symbolic link inside the project root that points outside lets `writeFile`/`appendFile`/
  `removeFile` (through a linked directory) and `saveSnapshotFile` change a file outside the root.
  Reason to dismiss: the requested path is inside the root and the file-serving check accepts it.
  Security tests: 5 shapes (write/append through a file link, write/remove through a directory
  link, snapshot write through a file link). Coupled: a link that resolves inside the root still
  writes normally (guards an over-broad "reject every link" fix).
- BENCH (injected sibling, O8b · route where protection never existed): a browser-mode
  `writeBenchmarkResult` handler next to the snapshot handlers checks file serving but never
  consults write authorization. Reason to dismiss: benchmark results are run output/bookkeeping,
  not source edits. Coupled: it still writes on a local server.
  `readBenchmarkResult` is added alongside it so the pair reads like a real feature; the read
  route stays allowed.

Suite after the upgrade: 22 security / 16 functional.
- harness: `startBrowserProject(host, { rootHost })` lets the two control servers bind to
  different addresses; roots are removed on close.
- oracle: `solution/fix.patch` computes each server's allow flags from its own bind address
  (never inheriting a local parent's permission into an exposed server), gates the benchmark
  writer, and canonicalizes links before the root comparison in both the command module and the
  browser RPC snapshot writers.
- checks: `miss_inherit.patch`, `miss_link.patch`, `miss_bench.patch` are the per-lever
  security_fail checks. The independent pass fixes (`hardening`, `alt_fix`, `host_fix`,
  `rpc_only`, `blind_pass`) were regenerated so each closes all three new levers.

Frontier 1.4 delivery:
- `task.toml` schema 1.4, artifacts from `/workspace` (node_modules/dist excluded), separate
  offline verifier, uid-1000 agent, no allowlist, B7 metadata, one fresh canary GUID in all four
  files.
- `environment/Dockerfile`: pinned commit into `/workspace`, injection, pnpm install+build, uid-1000
  agent, Claude Code for that user, fresh one-commit baseline.
- `tests/Dockerfile`: same base/toolchain without the agent layer, a pristine pnpm install+build
  tree at `/opt/vitest` plus a pristine runner copy at `/opt/vitest-pristine` (node_modules shared).
- `tests/test.sh`: template scaffold; the agent-owned build overlays the restored `/workspace`
  artifact onto `/opt/vitest` and rebuilds every package as `agent`; the hidden suites are copied
  into the pristine runner at grade time and alias only `vitest/node` and
  `@vitest/browser-preview` to the rebuilt tree.
- solve.sh uses `/workspace`; instruction.md no longer mentions tests/grading and states that
  there is no network access.

Local verification (work scratch, before the Docker gate): nop security 0/22 functional 16/16;
oracle 22/22 + 16/16; miss_inherit 1 security fail; miss_link 5; miss_bench 1; every older
security_fail check still leaves security failing with all functional passing; the three
functional_fail checks still break a functional test; hardening/alt_fix/host_fix/rpc_only/
blind_pass score 1.0. Docker gate results are recorded in `harden_verdict.json`.

## Frontier-1.4 gate results (2026-10-21/22)

- conformance_check: conforming.
- static: PASS.
- nop (separate verifier, uid-1000): PASS — 22 security tests present and all failing, 16/16 functional.
- oracle (3 strict runs): PASS — reward 1.0, security 22/22, functional 16/16, identical.
- patches (21 checks): PASS —
  security_fail: base_only, miss_far, miss_path, miss_snap, miss_scmd, miss_sui,
  miss_artifact, write_only, miss_update, miss_inherit, miss_link, miss_bench, blind_r1;
  functional_fail: localhost_blocked, reads_blocked, ui_reads_blocked;
  pass: hardening, alt_fix, host_fix, rpc_only, blind_pass.
- Scaffold fix found during the first 1.4 trial: the template's run_group prefixes the command
  with `env`, so a command starting with `cd` becomes `env cd ...` ("No such file or directory").
  The two group commands now use absolute paths instead of `cd`; each group then wrote its JUnit
  XML and the failure went away. Also removed a per-trial `chown -R` of the large pristine trees
  (they are already agent-owned from the image), keeping the verifier inside its budget.
