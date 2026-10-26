# FAIRNESS — vitest-api-fs-authz-inj

Static pre-trial review (BUILDER.md 3h). I did not run Docker, trials, gates or tests, and did not
look up the upstream fix. Inputs read: `tasks/vitest-api-fs-authz-inj/instruction.md`, every file in
`tasks/vitest-api-fs-authz-inj/tests/`, `tasks/vitest-api-fs-authz-inj/solution/fix.patch`,
`tasks/vitest-api-fs-authz-inj/environment/{inject.patch,Dockerfile}`, `build/.../manifest.json`,
`build/.../notes.md`, all `build/.../checks/*.patch`, and the recorded trial/gate JSON.

## 0. State of the shipped files (read this first)

The shipped test and solution files are the **pre-revision** versions, while the environment and the
check patches are the **revised** versions. This is the root of the findings below.

| Artifact | Says | Evidence |
|---|---|---|
| `environment/inject.patch` | injected UI sibling is `saveSnapshotFile(id, content)`, writing `ctx.snapshot.resolvePath(id, …)` | inject.patch:59-70 |
| `tests/{security,functional}/ui_api.test.ts` | calls `ui.rpc.saveInlineSnapshot(ui.file, …)` | security:41, functional:31 |
| `solution/fix.patch` | gates a handler whose body is `return fs.writeFile(id, content, 'utf-8')`, setup.ts base blob `ae0e26b` | fix.patch:212-221 |
| current inject result | setup.ts blob `caa3027`; injected handler ends `return fs.writeFile(snapshotPath, …)` | inject.patch:44,68-69 |
| `tests/support/harness.ts` | `startBrowserProject(allowWrite: boolean)` builds a hand-made project from four boolean fields | harness.ts:71-85 |
| `notes.md` / `manifest` | claim `startBrowserProject(host)` using real config resolution, 8 security + 9 functional tests, pristine `/opt/vitest-verifier` | notes.md:58-81, manifest.seam_notes |
| `tests/test.sh` | old verifier: rebuilds `/app`, runs `$APP/node_modules/vitest/vitest.mjs`, no `/opt/vitest-verifier` | test.sh:22-45 |
| suite size | shipped: 7 security + 7 functional; trials recorded 0.625 = 5/8 security | trial_detail_deepseek.json:9 |

Consequence: the oracle (`solution/fix.patch`) does not apply to the tree the Dockerfile builds, and
several check patches (`miss_sui`, `miss_update`, `ui_reads_blocked`, `host_fix`) cannot exhibit their
declared result against the shipped tests.

## 1. Per-test fairness

Instruction references below are to `instruction.md`.

| Test (file::name) | What it asserts | Instruction basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| `security/ui_api.test.ts::a request to overwrite a registered test file does not change it` | Real `createVitest` with `api.host=0.0.0.0`; token client calls `saveTestFile`; file is byte-identical (errors swallowed) | L28-33 "no request … may create, modify, or delete any file on disk" | No. Host-based and config-flag fixes both pass; the harness genuinely binds `0.0.0.0` | low |
| `security/ui_api.test.ts::a request to run test files does not start a run` | `rerun` never reaches the stubbed `server.rerunFiles` | L28-33 "no request may cause test code to run" | Maybe, low: only a fix that gates inside `Vitest.rerunFiles` (bypassed by the stub) fails; that placement would also block local watch reruns, contrary to L39-43, so it is not the natural correct fix | low |
| `security/ui_api.test.ts::a request to run a single task does not start it` | `rerunTask` never reaches the stubbed `server.rerunTask` | L28-33 same sentence | Same as above | low |
| `security/ui_api.test.ts::a request to write a snapshot into a registered test file does not change it` | Calls `rpc.saveInlineSnapshot`; file unchanged | L28-33 "whichever of the server's operations is used" | No (it passes vacuously): `saveInlineSnapshot` does not exist in the shipped tree, so the call cannot touch the file whatever the fix does | medium (vacuous) |
| `functional/ui_api.test.ts::saves an edited test file` | Local host (127.0.0.1): `saveTestFile` writes the content | L39-43 "a developer can save an edited test file" | No | low |
| `functional/ui_api.test.ts::runs test files when asked` | Local: `rerun` reaches `rerunFiles` once with the file | L39-43 "run and re-run tests" | No | low |
| `functional/ui_api.test.ts::writes a snapshot into a registered test file` | Local: calls `rpc.saveInlineSnapshot(ui.file, content)` and asserts the file now contains `content` | L39-43 "write snapshots" (but the named operation is not in the repo) | **Yes.** The shipped tree defines `saveSnapshotFile`, not `saveInlineSnapshot`. No correct fix derived from the instruction adds a new `saveInlineSnapshot` handler, so the call cannot write and the assertion fails. `score.py` forces reward 0 on any functional failure | **high** |
| `functional/ui_api.test.ts::still rejects saving a file that was never registered` | `saveTestFile` on an unregistered path throws and creates nothing | L42-43 "Operations that name a file the server has not registered are rejected exactly as before" | No | low |
| `functional/browser_commands.test.ts::writes a file when writing is allowed` | Synthetic project with `allowWrite:true`; `writeFile` creates the file | L39-43 "have browser tests … write files" | No for the oracle-style fix. Note the harness signal is a config field named `allowWrite`, which the instruction never mentions; a fix with a differently named flag fails (see §5a) | medium |
| `functional/browser_commands.test.ts::appends to a file when writing is allowed` | Same synthetic project; `appendFile` appends `B` | same | Same as above | medium |
| `functional/browser_commands.test.ts::reads a file even when writing is disabled` | `allowWrite:false`; `readFile` still returns content | L37-38 "Reading files … must keep working regardless of where the server is bound" | No (a fix that gates reads too is a wrong fix, modelled by `reads_blocked`) | low |
| `security/browser_commands.test.ts::creating a file does not take effect` | Synthetic project with `allowWrite:false`; `writeFile` must not create | L28-33 "through whichever interface" | **Yes.** The only exposed/local signal is the harness-supplied `allowWrite` boolean. A correct fix that decides from the bind host sees no host in the fake project and cannot distinguish this case from the `allowWrite:true` functional case (they differ *only* in that field) | **high** |
| `security/browser_commands.test.ts::appending to a file does not change it` | Same synthetic project; `appendFile` must not change a seeded file | same | **Yes**, same mechanism | **high** |
| `security/browser_commands.test.ts::removing a file does not delete it` | Same synthetic project; `removeFile` must not delete | same | **Yes**, same mechanism | **high** |

**Cross-cutting proof of the browser-harness unfairness.** The security call passes `allowWrite=false`
and the functional call passes `allowWrite=true`; everything else about the project object is
identical (`harness.ts:71-85`): no `host`, no `browser`, and `vite` built by
`createVitest('test', { root, watch:false })` with no `api` options. Therefore no decision based on
whether the server is network-reachable can pass both. The grader can only be satisfied by a fix that
invents and reads a `allowWrite` configuration field — a name that appears nowhere in the instruction
and is listed in `manifest.leak_terms`. `checks/host_fix.patch` illustrates the impossibility: its
`isApiServerExposed(server)` returns `true` for `undefined` (host_fix.patch:146-149), so
`assertApiServerNotExposed(project.browser?.vite)` throws for every synthetic project and the two
functional browser writes fail; a host-based fix that instead treats "no server" as local fails the
three security tests. Either way a correct host-based fix cannot score 1.0.

## 2. Leniency (QUALITY, non-blocking)

Security properties: (i) no network write via the UI API; (ii) no network exec via the UI API; (iii) no
network write via browser commands; (iv) reads keep working; (v) local operations keep working;
(vi) unregistered files still rejected.

| Property / trap | Most plausible WRONG fix | Caught by a shipped test? |
|---|---|---|
| BASE write (`saveTestFile`) | Gate only browser commands | Yes: `security/ui_api.test.ts::a request to overwrite a registered test file does not change it`; `checks/base_only.patch` is the reverse miss and is declared `security_fail` |
| BASE exec (`rerun`, `rerunTask`) | Gate writes only | Yes: the two `security/ui_api.test.ts` rerun tests; `checks/write_only.patch` (it has no `allowExec` gates) |
| BASE `updateSnapshot` (exec + write) | Gate save/rerun/rerunTask but leave `updateSnapshot` open | **No.** No shipped test calls `updateSnapshot` (the manifest names one, but it does not exist). `checks/miss_update.patch` removes exactly that gate and would still score 1.0 |
| A-FAR (`writeFile`, `removeFile`) | Fix the reported UI API only | Yes: `security/browser_commands.test.ts::creating a file does not take effect` and `::removing a file does not delete it` (with `allowWrite:false`); `checks/miss_far.patch` leaves both ungated |
| S-CMD (`appendFile`) | Gate `writeFile` and `removeFile`, forget the appended sibling | Yes: `security/browser_commands.test.ts::appending to a file does not change it`; `checks/miss_scmd.patch` gates only write/remove |
| S-UI (`saveSnapshotFile`) | Gate `saveTestFile` and `updateSnapshot`, leave the mirrored snapshot handler open | **No.** The only snapshot security test calls the non-existent `saveInlineSnapshot`; no shipped test ever calls `saveSnapshotFile`. `checks/miss_sui.patch` does exactly this miss and cannot produce its declared `security_fail` |
| Refuse-all | Disable writes/exec everywhere | Yes (UI side): `functional/ui_api.test.ts::saves an edited test file` and `::runs test files when asked`; `checks/localhost_blocked.patch`. The browser functional tests are *not* affected because the synthetic project bypasses config resolution |
| Adjacent API (block reads) | Put the same write gate on reads | Partly: `functional/browser_commands.test.ts::reads a file even when writing is disabled` catches `checks/reads_blocked.patch`; blocking UI `readTestFile` is not tested, so `checks/ui_reads_blocked.patch` is unobservable |
| Browser-RPC writes (`saveSnapshotFile`, `removeSnapshotFile`, `onTaskArtifactRecord` attachments) | Leave them open | **No.** No browser-RPC test exists; manifest records them as `known_uncaught` |
| `onTaskUpdate` (client-injected results) | Leave it in place | No test; the oracle removes it. No file/exec effect, so acceptable |

Wrong fixes that no shipped test catches:

- leaving `updateSnapshot` open (manifest trap BASE lists it; no test);
- leaving the injected UI `saveSnapshotFile` open (S-UI; the shipped snapshot test is vacuous);
- leaving browser-RPC snapshot/artifact writes open (manifest `known_uncaught`);
- blocking UI `readTestFile` while exposed (`checks/ui_reads_blocked.patch` has no target test);
- gating only `config.api.allowWrite` but not `config.browser.api.allowWrite` (or vice versa): the
  synthetic harness sets every carrier to the same boolean, so a one-sided gate looks correct;
- gating `writeFile` only on the resolved root flag while the browser project flag stays open: same
  reason.

## 3. Hints (QUALITY, non-blocking)

- **L8-10:** "the UI opens and saves test files, starts and re-runs tests, updates snapshots, and
  reads and writes files on behalf of browser tests." This enumerates the operation set, including the
  `updateSnapshot` trap and the browser command family. Neutral wording: "A browser-based UI and the
  browser-mode test driver use it to interact with the running project."
- **L23-24:** "the server offers several operations that change files or run code, reachable through
  more than one of its interfaces." It announces that there are multiple sites/interfaces (the A-FAR
  and injected siblings). Neutral wording: replace with "This is one example, not the whole problem."
- **L31-32:** "whichever of the server's operations is used, through whichever interface, and
  whichever file or task the request names." The word "task" points at `rerunTask`. Neutral wording:
  "…and whichever target the request names." (This revision was claimed in notes.md but is not in the
  shipped instruction.)
- **L42-43:** "Operations that name a file the server has not registered are rejected exactly as
  before." Names the existing registered-file gate. It is needed to justify the functional test, so
  keep it, but it can be neutralised to "Operations that are rejected today must stay rejected."
- Low: L47 "for every operation and interface that can reach it" tells the solver to enumerate all
  sites. Keep the requirement, but "Fix the problem in the library itself, not only the example above"
  conveys it without stressing the multi-site search.

The instruction correctly does **not** mention `allowWrite`/`allowExec`. That is fine in itself, and
is precisely why the browser tests' dependence on those names (§1/§5a) is unfair.

## 4. Realism (QUALITY, non-blocking)

- **S-CMD `appendFile`** (inject.patch:9-19): plausible maintainer code — a small helper registered
  next to `writeFile` in `commands/index.ts`, reachable through the real dispatcher. It is not added
  to the client-side `BrowserCommands` typings and has no caller, which is mildly contrived. Low/medium.
- **S-UI `saveSnapshotFile`** (inject.patch:59-70): realistic name and behaviour; it mirrors the
  browser-RPC handler and is typed in `WebSocketHandlers`. No UI-client caller was added, but the
  handler is reachable over the real RPC. Acceptable.
- **The shipped UI snapshot test is not realistic.** It calls `saveInlineSnapshot`, a handler that
  does not exist in the shipped inject tree. This is an artifact of the partial reset, not a trap a
  maintainer wrote. High (delivery).
- **The browser command harness is not realistic.** `startBrowserProject(boolean)` fabricates a
  project object (`harness.ts:71-85`) instead of using real config resolution; it never exercises the
  producer (`resolveApiServerConfig`) and never binds a browser API server. High; this is also the
  unfairness mechanism.
- **`solution/fix.patch` is stale.** It is based on setup.ts `ae0e26b`, while the shipped inject
  produces `caa3027`; its hunk expects `return fs.writeFile(id, …)`, which does not exist in the
  shipped `saveSnapshotFile` handler. `solve.sh` (`set -e`, `patch -p1`) will fail. High (delivery).
- **`test.sh` is stale** relative to notes/manifest: it runs the agent-rebuilt
  `$APP/node_modules/vitest/vitest.mjs`, not the claimed pristine `/opt/vitest-verifier`, and
  `pnpm build … || true` silently grades stale dist on build failure. Medium (grader integrity).
- Check patches are generated against the revised tree (`caa3027`, `saveSnapshotFile`), while the
  tests are old, so the declared pass/fail matrix cannot be reproduced against the shipped suite.

## 5. Verdict

### a. UNFAIRNESS gate — **NOT READY**

Two independent mechanisms make a correct fix fail the grader.

1. **Contradiction between the tests and the repository (deterministic, all solvers).**
   `functional/ui_api.test.ts::writes a snapshot into a registered test file` calls
   `rpc.saveInlineSnapshot`, but the tree built by `environment/Dockerfile` + `environment/inject.patch`
   defines `saveSnapshotFile`, not `saveInlineSnapshot`. No correct fix from `instruction.md` would add
   a handler that is absent from the product; the file is therefore never written and the test fails.
   `score.py` returns 0 when any functional test fails, so every correct fix scores 0. The shipped
   `solution/fix.patch` is itself built against the old `saveInlineSnapshot` tree and does not apply.
   **Exact change:** either (a) change both `ui_api` tests to
   `rpc.saveSnapshotFile(ui.file, content)` and assert the resolver-computed snapshot path (as the
   revised sibling task does), then regenerate `solution/fix.patch` and every check patch against the
   current inject tree (`setup.ts` base `caa3027`) so the oracle gates `saveSnapshotFile`; or
   (b) revert `environment/inject.patch` to inject `saveInlineSnapshot` and keep the tests. Verify the
   oracle scores 1.0 either way.

2. **The browser harness forces an unspecified config field (`allowWrite`).**
   `startBrowserProject(false)` and `startBrowserProject(true)` differ only in four `allowWrite`
   booleans; there is no host anywhere. A fix that implements the instruction's stated trigger ("when
   the control server is reachable from the network") cannot deny the security case and allow the
   functional case. A host-based fix either fails the three security tests or the two functional
   writes — `checks/host_fix.patch` fails the functional ones under this harness. The only passing
   design is one that invents an `allowWrite` option, a leak term absent from the instruction.
   **Exact change:** rewrite `tests/support/harness.ts::startBrowserProject` to take `host` and build a
   real project through `createVitest('test', { root, watch:false, api:{ port:0, host } }, …)` with a
   browser project whose `browser.api.host` is the same host (preview provider), then
   `_initBrowserServers()` and pass the resolved project to the command functions (or drive
   `triggerCommand` through the browser dispatcher). Test `0.0.0.0` and `127.0.0.1`; set no
   `allowWrite` anywhere. Require `checks/host_fix.patch` (host-based, no config flags) to score 1.0.

Secondary (not needed for the verdict, but the same test/harness class): the UI rerun tests stub
`server.rerunFiles`/`rerunTask`, so a gate placed in those core methods is invisible. Low risk, since
gating there would also break legitimate local reruns.

### b. Quality to tighten (non-blocking)

- Add `updateSnapshot` security (exposed: no call, with and without a file) and functional (local: one
  call) tests; `checks/miss_update.patch` is currently unobservable.
- Add the S-UI `saveSnapshotFile` security test and its local functional counterpart (or align
  inject), so leaving the injected handler open is caught.
- Add a functional `readTestFile`-while-exposed test; `checks/ui_reads_blocked.patch` is unobservable.
- Add a browser-RPC write test for `saveSnapshotFile`/`removeSnapshotFile` (or accept the
  `known_uncaught` record).
- Regenerate `solution/fix.patch` and all `checks/*.patch` against the shipped inject base, and make
  `test.sh` use the pristine `/opt/vitest-verifier` runner described in the manifest (fail closed if
  the rebuild fails).
- Neutralise the instruction hints in §3.
