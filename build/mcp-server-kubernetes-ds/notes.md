# mcp-server-kubernetes-ds — build notes

- Start: 2026-10-24T03:53:29Z (pipeline), design work from 2026-10-24T03:55Z
- End: 2026-10-24T05:15Z
- Repo: flux159/mcp-server-kubernetes, pinned a7d6fd4 (v3.8.0), published fix d7890f5.
- Pattern A+B, track injected.

## One-line levers

- **T1 base (A, report site)**: every ordinary kubectl tool pushes caller values (`name`,
  `resourceType`, `nodeName`, `resource`, ...) into bare positional argv slots, where pflag reads
  `--server=...`/`--token=...`/`--kubeconfig=...`/`--as=...`/`--insecure-skip-tls-verify=...` as
  options; the pinned tree guards only `kubectl_generic`'s free-form `flags`/`args`
  (`src/security/kubectl-flags.ts:88`, called from `src/tools/kubectl-generic.ts:77`).
- **T2 far site (A, second binary)**: `helm` is a second CLI with different credential-flag names
  (`--kube-apiserver`, `--kube-token`, `--kube-ca-file`, `--kube-as-*`,
  `--kube-insecure-skip-tls-verify`); a guard shaped around kubectl names misses it
  (`src/tools/helm-operations.ts:160`).
- **T3 uncovered route / protection never existed (B, how)**: `port_forward` builds argv and calls
  `child_process.spawn` directly, so a fix that only swaps `execFileSync` call sites never sees it
  (`src/tools/port_forward.ts:10`; token is `` `${resourceType}/${resourceName}` `` at :88).
- **T4 shape trap (B, how)**: pflag accepts a short option's value attached with no separator
  (`-shttps://attacker`); name-only normalisation sees `shttps://attacker` and lets it through
  (`-s`/`--server`/`--server=` are covered, which makes the shape look done).
- **T5 coupled must-keep-working (functional)**: (a) every tool legitimately emits
  `--context <value>`, which the existing `DANGEROUS_FLAGS` set names as dangerous, and context
  selection is not a target redirect without `--server`/`--kubeconfig`; (b) a command line meant
  for the workload is passed after `--` (`exec_in_pod`, `kubectl_create` job/cronjob) and may
  legitimately contain its own `-s`/`-c`. A blanket "reject every argv token starting with -"
  breaks ordinary use, and scanning past `--` breaks in-workload commands.
- **S1 injected (second transport)**: `kubectl_logs` follow mode runs through a new
  spawn-based streaming helper (`src/utils/log-stream.ts`), not the shared synchronous executor;
  upstream fix never touches that module.
- **S2 injected (second surface)**: the MCP resource surface gains a raw `k8s://raw/...` read that
  shells `kubectl get` with the URI segments as positionals (`src/resources/handlers.ts`);
  upstream fix never touches resources.

Every lever sits under the one general property: no caller-supplied value may reach the cluster or
chart command line where the tool reads it as an option that changes the target, credentials,
trust or identity — however it arrives and however it is written — and such a request must be
refused with no side effect.

## Candidate sibling sites audit (all found in the pinned tree, then injected additions)

Real sites / routes (unmodified upstream):
1. `kubectl-flags.ts` helper itself (existing, guards only kubectl_generic's flags/args).
2. `kubectl-get`, `kubectl-describe`, `kubectl-apply`, `kubectl-delete`, `kubectl-create`,
   `kubectl-logs` (5 exec sites), `kubectl-patch`, `kubectl-rollout` (2), `kubectl-scale`,
   `kubectl-context` (6), `kubectl-operations`, `helm-operations`, `node-management` — all
   `execFileSync` call sites; covered by the published fix's import swap.
3. `exec_in_pod` — name positional before `--`; in-workload command after `--`.
4. `kubectl-create` — `-- <command>` for jobs/cronjobs (same `--` boundary).
5. `port_forward` — spawn, resourceType positional. **chosen (T3)**
6. `kubectl_context` set — `name.split("cluster/")[1]` is the value actually pushed (an adjustment
   after any input-level check). Kept as a security test for the check-after-adjustment class.
7. `kubectl_rollout` — name is prefixed with `resourceType/`, so injection is via `resourceType`.
8. `helm-operations` `cat`/`-f valuesFile` local file read, `--post-renderer` host execution,
   predictable `/tmp/values-*.yaml` — different properties, out of scope (one line each in report).
9. `resources/handlers.ts`, `kubernetes-manager.ts`, `kubectl-reconnect.ts`, prompts — no child
   process at pinned (injection candidates).
10. `kubectl_generic` `flags` values are joined as `--key=value`; a value is never re-parsed as a
    flag, so only its positional fields (`command`, `subCommand`, `resourceType`, `name`) and its
    `args` array are routes.

Injected siblings considered:
- **S1** `kubectl_logs` follow through a spawn streaming helper — chosen. Realistic: a follow
  stream outlives a synchronous call; separate helper module.
- **S2** raw resource read through kubectl — chosen. Realistic: second public surface, arbitrary
  kinds the typed client does not wrap.
- S3 drain via an async `execFile` runner — rejected: `getNodeStatus` runs first with the same
  nodeName, so the ordinary guarded path refuses before the sibling is ever reached; it cannot be
  isolated by a security test.
- S4 new `kubectl_top` tool with its own executor — rejected as the weakest form (a new tool is
  visible in the tool list; it is a where-type search cost, not a mechanism).
- S5 stored route (apply manifest -> `trackResource` -> cleanup shells `kubectl delete`) —
  rejected for this build: the only clean sink is a destructive cleanup that swallows per-resource
  errors, so the required client-visible refusal is not guaranteed; the complexity/risk is not
  repaid when T3/T4/T5 already carry the how-type load. Recorded here as the next candidate if a
  hardening round is requested.
- S6 `kubectl_context` rename via `execFile` — rejected: config commands do not contact a cluster,
  so the refusal would rest only on argv shape with no credential-redirection impact.

Why S1/S2 beat the others: both sit on a different mechanism from the fix's change point (a
long-running child process; a non-tool request surface) rather than on another call site of the
same executor, both are reachable through a real entry point, both are far from the report (a
different tool / a different request type), and each has its own reason to be dismissed (the
tool's normal path already looks guarded; resources are not a tool).

## Sites / routes / shapes the hidden security suite covers

- All ordinary kubectl tools listed above, driven through the real MCP server over stdio with a
  stand-in `kubectl`/`helm` in PATH: positioned `name`, `resourceType`, `nodeName`, `resource`,
  `subCommand` values carrying `--server=`, `--kubeconfig=`, `--token=`, `--as=`,
  `--insecure-skip-tls-verify=`.
- helm install/upgrade/uninstall and template mode with `--kube-apiserver=`, `--kube-token=`,
  `--kube-as-user=`, `--kubeconfig=`.
- port_forward `resourceType` (spawn path).
- Attached short-option shape `-s<url>` in kubectl_get name, kubectl_generic args and
  port_forward resourceType.
- kubectl_context set with `cluster/--server=...` (value only appears after the prefix strip).
- S1 follow mode and S2 raw resource read.

## Coupled must-keep-working behaviour (functional suite)

- Ordinary values: resource/release names, types, namespaces, selectors, output formats, chart
  references, node names.
- `--context <value>` on several tools (existing denylist names context; argv guard must not).
- In-workload command lines after `--` with their own `-s`/`-c`
  (`exec_in_pod`, `kubectl_create` job/cronjob).
- Each injected sibling's legitimate use: follow returns streamed logs; raw resource read returns
  the stub's JSON.

## Test seam

The real built entry point (`dist/index.js`) is started as a child process over MCP stdio with a
stand-in `kubectl`/`helm` first on PATH. The stand-ins record their argv; the tests assert the
recorded tokens, parsed the way pflag would parse them (stopping at `--`), contain no target /
credential / identity / TLS option, and that the request was refused. No product module is
imported by the hidden tests; a correct fix at any layer passes. Functional tests assert the same
stand-ins receive exactly the expected ordinary argv and that calls succeed.

## Not verified / risks

- `present_in_latest` for the uncovered routes: latest upstream (origin/main b2e82de) already
  guards port_forward and the attached-short-option shape in later commits than the published fix;
  recorded in the register as `no` with the later-commit references.
- pflag's treatment of a bare `-s` and of `-s<value>` is asserted from pflag semantics and checked
  against the project's later test suite; no real kubectl binary is available offline.
- The published fix itself scans past `--` and would break in-workload `-s`; the oracle
  deliberately fixes that (T5), so the reference fix is the published fix plus these corrections.

## Verification log (local, scratch tree + node 20/npm 9, then the gate in Docker)

- Hidden suite against the pinned+injected tree: security 0/36, functional 23/23.
- Hidden suite against the reference fix: 36/36 security, 23/23 functional.
- Hidden suite against the alternative tokenizer fix: 36/36, 23/23.
- Project unit tests (pristine pinned copies of kubectl-context + kubectl-reconnect, 9 cases)
  pass on pinned+injected, reference and alternative trees.
- Per-check local results (security pass/fail, functional pass/fail):
  - miss_base 14/22, 23/0
  - miss_helm 30/6, 23/0
  - miss_port_forward 33/3, 23/0
  - miss_shape 32/4, 23/0
  - miss_stream 34/2, 23/0
  - miss_resource 34/2, 23/0
  - check_after_adjustment 35/1, 23/0
  - reads_only 14/22, 23/0
  - crash_as_refusal 0/36, 23/0
  - overbroad 36/0, 3/20
  - hardening 36/0, 23/0
  - alt_fix 36/0, 23/0
  Every variant compiles with `npm run build`.
- Gate: static PASSED (no warnings, no product imports in tests). nop trial: security 0/36,
  functional 32/32 (23 hidden + 9 project), reward 0.0. oracle runs 1-3: reward 1.0, 68/68 each, identical (gate oracle PASSED).
  patches PASSED: miss_base 22 sec fails, miss_helm 6, miss_port_forward 3, miss_shape 4,
  miss_stream 2, miss_resource 2, check_after_adjustment 1, reads_only 22, crash_as_refusal 36
  (all with functional 0 failures); overbroad 20 functional failures; hardening 1.0; alt_fix 1.0;
  blind.patch is downstream and was skipped as designed.
