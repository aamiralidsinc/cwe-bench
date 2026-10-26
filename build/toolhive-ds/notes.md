# toolhive-ds — build notes (build-v1, pattern A+B, track injected)

Start: 2026-10-24T05:16Z (pipeline)
Plan written: 2026-10-24T05:28Z
End: (pending)

## Candidate
stacklok/toolhive, pinned `950c006b9e95e813dd45d8cc01c4ba96bdc18a9a`, published fix
`d8f40cb1599b8bf66657f2dfff15bfbfc236e712` (GHSA-QG2G-G9W3-M5H8 / CVE-2026-58197 /
GO-2026-6526), "Default network isolation to on for local MCP servers".

Flaw: `RunConfig.IsolateNetwork` decides whether a locally run MCP server container is put on
an internal network behind the egress proxy. Every front end that starts a server has to set
it; when no option is given the zero value (`false`) leaves the container on the host network.
The published fix flips the CLI flag default and makes the API request field a `*bool` whose
nil resolves to true.

## The one property (written before choosing routes)

> Every MCP server that ToolHive runs as a local container must be on a network isolated from
> the host. Isolation may be turned off only when the person starting that server explicitly
> asks, for that server, that it run without isolation. A definition that does not mention the
> setting is isolated; one that explicitly disables it is not. This holds however the server is
> started and whatever definition supplies its settings, including a definition saved earlier
> and started again. A server keeps the setting it already has; changing its version must not
> change that setting.

Everything below is covered by this text read literally. The report states it once and names
no route.

## Every candidate site / route found (screener O8/O8b + own search)

| # | route/site | where | kind | testable offline | decision |
|---|---|---|---|---|---|
| 1 | CLI `thv run` default | cmd/thv/app/run_flags.go:260 -> buildRunnerConfig:670 | reported, published fix | yes (buildRunnerConfig + flag parse) | LEVER L1 |
| 2 | HTTP API create, field omitted | pkg/api/v1/workload_types.go:75 + workload_service.go:342 | published fix far site (different package) | yes (WorkloadRoutes handler + mocks) | LEVER L2a |
| 3 | HTTP API update, field omitted | same schema, workloads.go:413 | published fix far site (operation) | yes | LEVER L2b |
| 4 | API GET response mapper | workload_types.go:360 | published fix | compiles with schema change | coupled |
| 5 | API export of a saved config | workloads.go:692 (raw RunConfig JSON) | untouched producer; `omitempty` drops false | yes | PRODUCER for L4 |
| 6 | CLI `thv run --from-config` | cmd/thv/app/run.go:459 + export.go | untouched real route (protection never existed) | yes (saved-state side effect; no Docker) | LEVER L4a |
| 7 | MCP `run_server` tool config builder | pkg/mcp/server/run_server.go:149-172 | untouched real route (protection never existed) | yes (buildServerConfig + fake registered runtime) | LEVER L3 |
| 8 | TUI run-from-registry | pkg/tui/actions.go:188-202 | untouched real route | no: ResolveMCPServer + EnforcePolicyAndPullImage need registry/Docker | rejected (untestable) |
| 9 | `--from-config` deserializer | pkg/runner/config.go:189 (`omitempty`), ReadJSON | producer | yes | part of L4 |
| 10 | upgrade applier | pkg/workloads/upgrade/applier.go:304 | untouched, preserves old value | yes (existing harness idiom) | coupled functional |
| 11 | restart | pkg/workloads/manager.go:1227 | untouched, reloads saved config | yes but same preservation | not a gap |
| 12 | vmcp embedding service direct deploy | pkg/vmcp/cli/embedding_manager.go:297 (false) | auxiliary container, not an MCP server workload | n/a | out of scope (one line) |
| 13 | inspector direct deploy | cmd/thv/app/inspector.go:142 (false) | auxiliary container | n/a | out of scope (one line) |
| 14 | operator builder | pkg/runner/config_builder.go:919 | Kubernetes; isolation not applicable | n/a | out of scope (one line) |
| 15 | permission profile network host/none | pkg/container/docker/client.go:1571 | bypass by design (explicit network mode) | n/a | out of scope (one line) |
| 16 | builder initial default | pkg/runner/config_builder.go:946 | common producer; every front end overrides it | yes | alternative fix |
| 17 | **injected: API bulk import of saved definitions** | pkg/api/v1 (new file + route) | second implementation of replay, different package | yes (HTTP handler + mocks) | LEVER L4b (injected) |

Why the picks beat the rest:
- #7 (L3, real): highest-value category ("protection never existed"), far package, plausible
  dismiss ("agent-facing experimental control tool with a minimal arg set"), and it is real
  upstream code the published fix never touches.
- #6/#9 (L4a, real + producer): a how-type pair. The route is real and untouched; the
  `omitempty` producer silently drops an explicit false, so the check (default on when the
  definition is silent) and the producer (record an explicit false when one exists) must both
  be fixed, and they are on separate paths. Dismiss: "a saved config is a complete explicit
  specification, replay it literally".
- #17 (L4b, injected): a second implementation of the same replay in a different package so a
  solver who fixes only the CLI copy still leaves it open. Dismiss: "the import endpoint is the
  API face of the CLI path; it must already share the handling".
- #8 TUI was the obvious third real route but its builder cannot run offline (registry resolve
  + image pull), so it is recorded and not relied on.
- #11 restart / #10 upgrade preserve the stored value; they are the coupled must-keep-working
  (an over-broad sink fix or a `ReadJSON`-wide default breaks them).

## Levers and reasons to dismiss

- **L1** CLI default (reported): report leads here; a fix that only changes the flag passes L1.
  Reason to skip: none (reported).
- **L2a** API create with the field omitted (far site, other package). Reason to skip: "the
  report shows the CLI; the API is a different surface".
- **L2b** API update with the field omitted over an existing workload. Reason to skip: "the
  edit operation reuses the create schema, so the create fix covers it" (a handler-level fix
  that only defaults at create does not).
- **L3** MCP `run_server` builder (real, protection never existed). Reason: experimental
  agent-facing control tool, minimal args, "inherits whatever the builder does".
- **L4a** replaying a saved definition through the CLI (real). Reason: "a config file is an
  explicit full specification; replay it literally". How-type: the shared deserializer cannot
  tell absent from false, and the exporter is a producer the check never calls.
- **L4b** replaying a saved definition through the injected API import (second implementation).
  Reason: "the CLI already handles saved definitions; this is the same path".

How-type coverage: L4a/L4b need the mechanism understood (presence of the field vs its zero
value, and the producer that drops false). L3 is the "route where the protection never existed"
shape. L2b is an operation distinction; L1/L2a are the base.

## Coupled must-keep-working (functional)

- explicit `--isolate-network=false` still starts non-isolated;
- explicit `network_isolation: false` on create and on update still starts non-isolated;
- explicit `true` stays isolated;
- a server whose stored setting is explicitly false keeps it when its version changes
  (upgrade applier preserves `old.IsolateNetwork`; an old saved config that omits the field
  must still load as false — so a default must not be put in the shared deserializer);
- an exported explicit-false definition records the false, and starting that saved definition
  keeps it non-isolated;
- ordinary create/update still return the same success response and keep
  name/image/transport/ports/env/volumes;
- the project's own tests for the affected area pass.

## Security tests (entry point, harmless expected value)

- CLI: `AddRunFlags` + `buildRunnerConfig` with no isolation option -> RunConfig.IsolateNetwork
  true; explicit false -> false.
- API create: `WorkloadRoutes.createWorkload` over HTTP, body omits the field -> captured
  RunConfig true.
- API update: `WorkloadRoutes.updateWorkload` over HTTP, body omits the field -> captured true.
- MCP: `buildServerConfig` (the `run_server` tool's builder) with a registered fake runtime ->
  RunConfig true.
- CLI saved definition: `runFromConfigFile` on a definition that omits the field -> the saved
  state (what the detached worker loads) has true.
- API import (injected): `WorkloadRoutes.importWorkloads` over HTTP with a definition that
  omits the field -> captured RunConfig true.
- Explicit false on each of those -> false (functional side).

## Injected code (environment/injection.patch)

One sibling: `pkg/api/v1/workloads_import.go` + a `POST /api/v1beta/workloads/import` route
registered in `workloads.go`. It decodes previously exported run definitions and starts them
through a service method that builds the RunConfig itself (not the shared create path). It is
ordinary maintainer code: an API face for the existing CLI "run a saved configuration" flow.
It never appears in the report; it is covered only by the general property.

## Out of scope (one line each)

- Auxiliary containers (inspector, embedding service) are not MCP server workloads.
- Operator/Kubernetes does not consume the flag.
- Permission-profile `network_mode: host|none` bypasses isolation by explicit choice.
- Port/egress proxy mechanics are not exercised (RunConfig level only, no Docker).

## What I verified / could not verify

- Verified at the pinned commit: API create/update omit -> false; CLI builder omit -> false;
  MCP builder -> false; `--from-config` omit -> false in saved state; each reachable offline
  with fakes (probe tests run locally).
- Could not verify: the current upstream state of the real routes (no read-only look at latest
  yet); TUI route behaviour offline; whether Docker is present in the verifier (tests avoid it).

## As built (2026-10-24T05:50Z)

Injected (environment/injection.patch): one new file `pkg/api/v1/workloads_import.go` and a
`POST /api/v1beta/workloads/import` route. It decodes previously exported run definitions and
starts them through a service method that builds the RunConfig itself; ordinary maintainer code
for the API face of the CLI's existing saved-configuration flow.

Reference fix (solution/fix.patch) turns isolation on at every start decision and keeps the
producer honest:
- run command flag default;
- API request schema `*bool` with nil resolving on, used by create and edit (plus the response
  mapper and the existing project test updated for the pointer);
- MCP run-server builder sets isolation explicitly;
- CLI saved-definition replay detects an omitted field and defaults it on;
- injected API import does the same;
- the serialised run configuration records an explicit false instead of dropping it, so a saved
  opt-out survives export and replay; the shared deserialiser is deliberately left alone.

Hidden suites (staged into the product packages at grade time):
- security: APICreate/APIUpdate/APIImport omitted; RunServerTool; CLI run default; SaveDefinition default.
- functional: explicit opt-out/opt-in on API create, update, import, CLI; saved opt-out round trip;
  saved isolated round trip; ordinary create keeps fields; version-change preserves an explicit
  opt-out; an existing stored definition is not rewritten; project tests
  TestApplier_Apply_PreservesFullUserConfig and TestRunConfig_WriteJSON_ReadJSON.

Check patches (build/toolhive-ds/checks): sf-miss-cli, sf-miss-api, sf-miss-mcp, sf-miss-fromcfg,
sf-miss-import (security_fail); sf-miss-producer, ff-overbroad (functional_fail);
pass-hardening (oracle + builder-level defensive default); pass-alt (no pointer: handler-level
presence detection plus a builder default for the tool). All apply cleanly to the injected tree
and build; oracle/nop/pass-alt were exercised locally.

Local suite results: vulnerable tree — all 6 security tests fail, all functional pass; reference
fix and pass-alt — all pass. sf-miss-producer fails only the saved-opt-out round trip.

Out of scope (one line each): auxiliary containers (inspector, embedding) are not MCP server
workloads; the Kubernetes operator does not consume the option; a permission profile that selects
host/none bypasses isolation by explicit choice; the TUI route is real but its builder cannot run
offline, so it is recorded and not relied on.

## Gate (2026-10-24)

- static: PASSED.
- nop: PASSED — security 0/6 pass (all fail on the vulnerable tree), functional 13/13 pass, reward 0.0.
- oracle: PASSED — 3 runs, reward 1.0 each, 19/19 tests (6 security + 13 functional), identical results.
  (The first oracle attempt was interrupted by the host Docker deadlock; after the host fix the
  stage was rerun from scratch on the system daemon and passed.)
- patches: running (9 checks).

Note: an earlier nop attempt failed because `test.sh`'s `CLEAN_ENV` cleared `GOPATH`/`GOMODCACHE`,
so the offline verifier tried to download modules; the env arrays now carry the image's Go cache
paths and `GOPROXY=off`.

## Final gate (2026-10-24T09:55Z)

All four stages pass on the system Docker:

- static: PASSED
- nop: PASSED — security 0/6, functional 13/13, reward 0.0
- oracle: PASSED — 3 runs, reward 1.0, 19/19 each, identical
- patches: PASSED — 9 checks:
  - sf-miss-cli: 1 security fail (TestSec_CLIRunDefaultsToIsolation), 0 functional
  - sf-miss-api: 2 security fails (APICreate/APIUpdate), 0 functional
  - sf-miss-mcp: 1 security fail (RunServerTool), 0 functional
  - sf-miss-fromcfg: 1 security fail (SavedDefinitionDefaults), 0 functional
  - sf-miss-import: 1 security fail (APIImportOmitted), 0 functional
  - sf-miss-producer: functional fail (saved opt-out round trip), reward 0
  - ff-overbroad: 4 functional fails, reward 0
  - pass-hardening: reward 1.0
  - pass-alt: reward 1.0

The `blind` pass patch is not written by me (the pipeline writes it after this build); the
manifest lists it as required by strict_gate.

## Could not verify / guesses

- The TUI route is real and unprotected but was not built or tested: its builder needs a registry
  resolve and an image pull, so it cannot run offline. Recorded in the register and left out of
  the reference fix (it is not a route in the task).
- `present_in_latest` for the two real routes was checked by fetching the current upstream tree
  read-only: the CLI saved-definition path and the `omitempty` producer are still present and
  unchanged; the MCP run-server file is gone from the latest tree (refactored away).
- The agent/verifier images are large (repository module cache ~2 GB; the built environment
  image measured ~10.6 GB), so storage was raised to 20 GB. If Harbor's quota counts the image,
  this is the main resource risk.
