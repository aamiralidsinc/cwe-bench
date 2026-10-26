# vitest-api-fs-authz-inj — build notes

- Start (UTC): 2026-10-18T02:33Z
- End (UTC):   2026-10-18T03:15Z

## Advisory
GHSA-5XRQ-8626-4RWP / CVE-2026-47429, vitest-dev/vitest. Missing authorization on the
network-reachable test-runner control API plus path confinement (CWE-862 / CWE-22).
Pinned (vulnerable) commit 76c4397b58618b6b430b0800487995c77bb6dad7 — verified to be the parent
of the published fix 20e00ef7808de6d330c5e2fda530f686e08f1c8d. Track: injected. Pattern: A+B
(see below for what was actually realized).

## Levers (one line each)
- BASE (A, reported): UI control-server write/exec RPC handlers — packages/vitest/src/api/setup.ts saveTestFile (write) + rerun/rerunTask/updateSnapshot (exec). Dismiss: n/a (reported).
- A-FAR (A, far site, second implementation): browser-mode file commands writeFile/removeFile — packages/browser/src/node/commands/fs.ts (different package). Dismiss: "separate browser-test server, writes are the user's own test code, gating looks like breaking browser tests."
- S-CMD (injected sibling): extra browser file command appendFile with the pre-fix pattern — fs.ts + commands/index.ts. Dismiss: "convenience append helper, not the create/delete pair named."
- S-UI (injected sibling): extra UI write handler saveInlineSnapshot gated only by registered-file membership — setup.ts + api/types.ts. Dismiss: "inline-snapshot editor action on an already-registered file."
- Producer (enforced, not a standalone test): resolveApiServerConfig defaults (localhost/unset -> allow, network host -> deny, browser.api inherits) is forced by the exposed-refuses + localhost-works test pair.

## What I verified (locally, offline, repo's own toolchain)
- The flaw reproduces through the real entry point: a client connected to the LIVE UI control
  server (createVitest with api host 0.0.0.0, watch:true, token from config, driven by a minimal
  birpc client over ws) overwrites a registered test file and starts runs at the pinned+injected
  commit; the browser file command functions create/append/remove files with writes disabled.
- nop (pinned+inject): all 7 security tests FAIL, all 7 functional PASS.
- oracle (inject+fix.patch): all 14 tests PASS; localhost save/run/snapshot and browser
  write/append + reads all keep working.
- All 8 check patches behave as declared (counts recorded): base_only/miss_far/miss_scmd/
  miss_sui/write_only -> security_fail; localhost_blocked/reads_blocked -> functional_fail;
  hardening/alt_fix -> pass.
- fix.patch applies cleanly to the pinned+inject tree with `patch -p1`; inject.patch applies to
  the pinned tree. fix.patch excludes the unrelated packages/utils/src/source-map.ts noise from
  the upstream commit.

## What I could not / did not do
- Pattern-B uncovered routes were investigated and DISMISSED, not built (register rows added):
  (1) the UI source-viewer read handlers' deprecated serving check is a NO-OP to "fix" in this
  tree — in vite 7.1.5 the stricter loading check also returns true when server.fs.strict=false,
  so the published fix's read-path switch does not actually confine reads here; not fix-closable,
  read-only. (2) The browser-mode RPC snapshot/artifact write handlers are already covered by the
  published fix and need a live Playwright browser provider to drive, which is not offline/
  deterministic. So the realized task is Pattern A (reported + far site) + 2 injected siblings.
- The project's browser/UI Playwright e2e specs were deliberately not used (GUI/flaky/offline).
  Their config-resolution coverage is reproduced offline via createVitest.
- Docker gate stages (static/nop/oracle/patches) are to be run by builder/gate.py on the shared VM.
- FAIRNESS.md and the blind pass-patch are intentionally left for the post-build step.

## Fairness note
Everything the tests require is reachable from instruction.md + code: the instruction states the
invariant generically ("no request ... may create, modify, or delete any file ... or cause test
code to run ... whichever operation, through whichever interface, and whichever file or task")
which covers the far site and both injected siblings without naming them. The two injected
siblings sit beside real handlers with the same pre-fix shape, so a careful engineer enumerating
the control-server's file/exec operations finds them. Residual risk: the published fix introduces
the user-visible write/exec options and the local-vs-network default rule; the instruction conveys
this as "reachable from the network -> refused, local -> works" without naming the fields.

## Fairness revision (2026-10-18)
Addresses FAIRNESS.md "Required changes". Per-test results of the 6 earlier trials (3 deepseek,
3 mimo, all 0.5714) were checked: every run failed exactly the 3 browser_commands security tests,
i.e. the old synthetic-project harness, not the models. Those trials are not evidence of difficulty.
1. Harness: startBrowserProject(host) now resolves a real browser project: createVitest with
   api.host = host plus an inline project whose browser.api.host = host (preview provider), then
   _initBrowserServers(); the browser vite server really binds the host. No allowWrite in tests.
2. checks/host_fix.patch: host-based design (blind_r1 + appendFile + saveSnapshotFile gates), no
   config flags; 1.0. Oracle, hardening, alt_fix also 1.0 under the new harness.
3. Old blind.patch -> checks/blind_r1.patch, expect security_fail (missed both siblings). Fresh
   blind pass patch is wired separately.
4. updateSnapshot: security (exposed: no call, with and without a file) + functional (local: one
   call); checks/miss_update.patch.
5. functional/ui_api: readTestFile works while exposed; checks/ui_reads_blocked.patch.
6. instruction.md: L7-9 / L22-24 reworded neutrally; "file or task" -> "target".
7. S-UI replaced: saveSnapshotFile(testFile, content) writes the test's snapshot file (resolver
   path), mirroring the browser RPC handler of the same name. inject/fix/all check patches were
   regenerated mechanically (same gates, new handler body).
8. Browser-RPC snapshot/artifact routes recorded in manifest.known_uncaught. Verifier runner pinned:
   Dockerfile copies /app/packages to /opt/vitest-verifier after pnpm build; test.sh runs that
   runner with tests inside the copy and aliases vitest/node, the browser command source and the
   preview provider to /app.
Local verification (scratch repo, pristine-runner layout): nop 0/8 sec, 9/9 fun; oracle 1.0;
host_fix/hardening/alt_fix 1.0; every security_fail/functional_fail patch as declared.

## Fairness revision restored (2026-10-20)

The reset that followed the 2026-10-18 revision left the shipped `tests/` and
`solution/fix.patch` at their pre-revision state while `environment/inject.patch`,
`checks/*.patch`, `notes.md` and the manifest kept the revised versions (FAIRNESS.md §0).
The 2026-10-18 revision was restored and re-verified:
1. `tests/support/harness.ts`: `startBrowserProject(host)` builds the project through
   real config resolution (`createVitest` with `api.host`, an inline browser project with
   `browser.api.host = host` and the preview provider), calls `_initBrowserServers()` and
   drives the file commands through the browser API `triggerCommand` RPC. No `allowWrite`
   anywhere. Both `0.0.0.0` and `127.0.0.1` are exercised.
2. UI tests call the handler the tree actually defines, `saveSnapshotFile`, and assert the
   resolver-computed snapshot path. `updateSnapshot` security (exposed, with and without a
   file) and functional (local) tests added; a functional `readTestFile`-while-exposed test
   added.
3. `solution/fix.patch` and every `checks/*.patch` are the regenerated versions based on
   setup.ts `caa3027` (S-UI = `saveSnapshotFile`). `host_fix` is a config-flag-free,
   host-based independent fix and scores 1.0 under the real-config harness.
4. `tests/test.sh` runs the pristine `/opt/vitest-verifier` runner with the product aliased
   to `/app`, and fails closed (no test run -> score 0) if the rebuild fails.
5. `instruction.md`: operation enumeration removed; "several operations ... more than one
   interface" and "file or task" neutralised; registered-file sentence generalised.
6. `blind_r1` stays recorded honestly as `security_fail` (it missed both injected siblings);
   a fresh `kind=blind expect=pass` patch is wired separately, so static reports only that
   missing item.

Gate (2026-10-20): nop PASS (0/8 sec, 9/9 fun), oracle PASS (3 runs, 1.0),
patches PASS (all 13 declared checks), static PASS except the separately wired blind patch.
Local pristine-runner re-runs: nop 0/8+9/9, oracle 1.0, host_fix 1.0, miss_update 0.875
(updateSnapshot security test fails), ui_reads_blocked functional fail (UI read test).
