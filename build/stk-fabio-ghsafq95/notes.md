# stk-fabio-ghsafq95 build notes

- Start: 2026-10-23T05:30Z (resume pass; the prepared `tasks/` tree and `build/…/manifest.json`
  had disappeared between pipeline passes, so both were re-derived from the verified scratch
  artifacts and re-gated).
- End: 2026-10-23T07:04Z.

## Stack (pattern H3b, A+B)

- Advisory A = GHSA-q7p4-7xjv-j3wf, fix `fdaf1e966162` (a merge whose first parent is the pinned
  `66acfbb0`): filter the hop-by-hop declaration against a hard-coded set of the well-known
  forwarding headers.
- Advisory B = GHSA-fq95-v8xc-jm3v (incomplete fix of A), fix `240526a80040`: also protect the
  operator-configured client-address, transport and request-id header names. B sits on a later
  tree; `checks/upstream_fix.patch` is the same three edits reduced onto the pinned tree.
- Pinned rule: first parent of A's merge commit, confirmed with `git show --format=%P`.

## Levers (one line each)

- **T2** (published-fix far site, deepseek, concept C1): the client-address and transport header
  names come from operator configuration (`proxy/http_headers.go:45-48`, `126-130`,
  `config/load.go:149-151`), so A's hard-coded list misses them. Reason to dismiss: the reported
  header is well known and a list of well-known forwarding names looks complete.
- **T3** (published-fix far site, deepseek, concept C1): the request id is written in the request
  handler (`proxy/http_proxy.go:88-94`, `config/load.go:152`), outside the header builder, and reads
  as a correlation value. Reason to dismiss: correlation values look non-security and the write is
  not where the other headers are built.
- **T4** (uncovered route + coupled value, both, concept C2): when the operator designates the
  well-known client-address header, `proxy/http_headers.go:45-53` still skips writing it and keeps
  the client-supplied value; the pinned unit test pins preservation for the default configuration.
  Reason to dismiss: the project does this on purpose for chained proxies and a test pins it.
- **T6** (uncovered route, deepseek, concept C3): `proxy/grpc_handler.go:52-58` copies every client
  metadata entry to the outgoing context; `main.go:178` wires the gRPC listener to that director.
  Reason to dismiss: a transparent pass-through that never set derived headers reads as a missing
  feature rather than a vulnerable route.

Concepts (the reference fix's independent edit sites): C1 = {T2,T3} (one hop-by-hop sanitiser whose
protected set includes the configured names), C2 = {T4} (the designated client-address value),
C3 = {T6} (the other forwarding path). Three independent concepts; DeepSeek-type T2/T3/T6 and
MiMo-type T4.

**Dropped levers.** T1 is the reported, easy route; five security tests cover it but it is not a
lever. T5 (raw websocket forwarding) needs a hop-by-hop-honouring intermediary to cause harm and is
kept as must-keep functional coverage. T7 (a declaration split over several lines) was checked
behaviourally: a first-value parser drops the whole declaration and therefore blocks the attack, so
it is kept as a functional case where a naive parser drops a legitimate upgrade token.

## Verified in this pass

- Re-derived tree byte-compared with the artifacts of the earlier green runs: the oracle workspace
  after `solution/fix.patch` is identical (md5) to the workspace the 02:47 oracle run scored 1.0
  with; likewise the control oracle workspace vs the 02:19 control run.
- Local (host Go, real binary over loopback): pinned tree 11/11 security fail, 10/10 functional
  pass; reference 11/11 + 10/10 pass; control pinned 5/5 security fail, 10/10 functional pass.
- Every check patch re-applied to a clean pinned tree, built and run locally; outcomes matched the
  declared ones (details below and in `verify-checks.txt` next to this task's work dir).
- Stability: the pinned binary run three times gives the same outcome each time (security fails,
  functional passes); the reference binary run three times gives 21/21 each time.
- Project tests for the affected area pass on the pinned tree in the environment image (run at
  image build, not in the graded group).
- No advisory regression test exists at the pinned commit (`git grep` for the sanitiser identifiers
  and the declaration filtering at HEAD finds nothing); both fix commits add them.

## Local check matrix (this pass, full line-by-line log in evidence/)

Each check patch applied to a clean pinned tree, built and run against both suites on the host:

| patch | security tests failing | functional tests failing |
|---|---|---|
| miss_concept_connection (= sf-hardcoded-list) | ConfiguredClientIP, RequestID | none |
| miss_concept_clientip (= sf-no-clientip-overwrite) | DesignatedClientIP | none |
| miss_concept_grpc (= sf-no-grpc-protection) | 3 gRPC tests | none |
| sf-no-connection-protection | 7 (T1/T2/T3) | none |
| sf-crash-on-attack | 7 (T1/T2/T3) | none |
| ff-refuse-connection | 8 | 9 |
| ff-overwrite-xrealip | none | PreservesClientRealIP |
| ff-single-line-parser | none | WebsocketDeclarationAcrossLines |
| upstream_first_fix (A alone) | 6 (T2,T3,T4,T6) | none |
| upstream_fix (A+B) | 4 (T4,T6) | none |
| pass-alt | none | none |
| pass-hardening | none | none |
| control cf-sf-no-sanitiser | 5 (all control security) | none |
| control cf-ff-refuse-connection | 5 | 9 |
| control cf-pass-hardening | none | none |

The one difference from the first pass's recorded matrix is `ff-refuse-connection`: the
`AppendsForwardedForChainWhenConfigured` functional test was added after that recording, so it now
fails too (the declared outcome only requires at least one functional failure).

## Gate (this pass)

- static: PASSED.
- nop: PASSED — 11/11 security tests failing, 10/10 functional passing on the pinned tree
  (trial `stk-fabio-ghsafq95-nop-1792733794`).
- oracle: PASSED — 3/3 runs at reward 1.0, 21/21 tests each, identical result maps
  (`oracle1-1792734133`, `oracle2-1792734336`, `oracle3-1792734615`; the first oracle3 launch
  collided with another Harbor job and the gate retried once, as designed).
- patches: PASSED — 12/12 checks behaved as declared:
  - `miss_concept_connection` 2 security failing (T2, T3), functional all passing;
  - `miss_concept_clientip` 1 (T4); `miss_concept_grpc` 3 (T6);
  - `sf-no-connection-protection` 7; `sf-crash-on-attack` 7;
  - `ff-refuse-connection` 9 functional failing; `ff-overwrite-xrealip` 1; `ff-single-line-parser` 1;
  - `upstream_first_fix` 6 security failing (the published first fix is a wrong fix);
  - `upstream_fix` 4 security failing (T4, T6 — the complete published fix is a wrong fix for this
    task);
  - `pass-alt` 1.0; `pass-hardening` 1.0.
- control (`stk-fabio-ghsafq95-control`): static PASSED; nop PASSED (5/5 security failing, 10/10
  functional passing); oracle PASSED 3/3 at 1.0 (15/15 each); patches PASSED 3/3
  (cf-sf-no-sanitiser 5 security failing; cf-ff-refuse-connection 9 functional failing;
  cf-pass-hardening 1.0).

## Not verified / guesses

- No target-model trial was run (as instructed), so the bar itself is untested here.
- The reader labelled T6 `injection_room`; it is real, unmodified upstream code, so it is recorded as
  `uncovered_upstream`. Nothing was injected anywhere in this task.
- Whether upstream regards T4 or T6 as in scope of GHSA-fq95-v8xc-jm3v was not established; the
  task's stated property covers them, as the stacked rules require.
- The score (0.28) is the reader's upper-bound estimate, not calibrated by trials.
- The gRPC request id is derived with the in-repo UUID generator; a solver may use another source,
  and the test only requires a non-empty value that is not the client's.

## Fairness

- The report states two general properties and no surface, file, route or mechanism beyond the one
  reported trigger. It names no protocol, path or stage.
- The coupled functional tests keep the pinned chained-proxy behaviour (client-supplied `X-Real-Ip`
  when no header is designated, `X-Forwarded-Host` pass-through, the `X-Forwarded-For` append), the
  configured client-address and request-id headers on ordinary requests, ordinary hop-by-hop
  stripping, protocol upgrades (including a declaration split over two lines) and unchanged
  non-derived metadata on the other path, so a blanket-removal or blanket-overwrite fix fails.
- The transport-assertion contract is stated explicitly (present only when the connection was
  secured), so a fix on the second path is not asked to guess the absent value.

## Pattern B register

`build/audit/uncovered-routes.tsv` carries one row per hidden route (T4 and T6): real upstream
code, still present in current upstream HEAD (`5b4c4285`), no public report, in scope (B), built,
`pending client decision`.

## Out of scope (one line)

- Nothing was built outside this advisory's own protection in fabiolb/fabio at the pinned commit;
  no other project or advisory was touched.

## Revision 2026-10-24 (instruction-only, AUDIT-FIX-20261024)

- Required 1: the removal/alteration/substitution rule is scoped to values the proxy sets and to
  headers the operator designates for a trust value, so the coupled preservation tests are no longer
  contradicted; the intro's "rather than whatever the client supplied" was dropped.
- Required 2: one general sentence now states that for every header the operator designates to
  carry a trust value the backend receives the proxy's own value on every path the proxy serves.
- No test, oracle, manifest, trap or check patch changed (the audit says they were correct).
- `FAIRNESS.md` written with the test table and the "Stacking checks" S1-S7 section.

### Gate (this revision)

- static: PASSED.
- nop: PASSED — 11/11 security tests failing, 10/10 functional passing on the pinned tree.
- oracle: PASSED — 3/3 runs at reward 1.0 (21/21 each).
- patches: PASSED — 12/12 as declared (concept misses 2, 1 and 3 security failing; sanitiser-removal
  and crash shapes 7 each; three functional-fail shapes at reward 0.0; upstream A 6 and A+B 4
  security failing; alternative and hardening at 1.0).

### Listing check (build rule 7)

- FAIL `named=0 described=4`: the Required-2 clause "the operator designates a header to carry a
  trust value" is the contract T2/T3/T4 need, and "on every path the proxy serves" is the contract
  T6 needs; both are DESCRIBED under the v3 one-bug test, so no wording that states the required
  contract can pass. Same fairness-vs-listing conflict as comfyui-manager-2366; reported in
  `FAIRNESS.md` for a human decision rather than dropping the required contract.

## Revision 2026-10-25 (instruction-only, AUDIT-FIX-20261025)

- Required 1: the impact example no longer names `X-Real-Ip`. Both mentions were replaced by
  "a forwarding header the proxy had just set" / "no such header at all", so the example names no
  specific header and still shows only the symptom (the reported removal case). Nothing else in
  instruction.md changed.
- Required 2: no test, oracle, manifest or check patch changed; only instruction.md, FAIRNESS.md
  and this note were edited. The tests, fix and checks stay byte-identical to the gate-green
  2026-10-24 revision.
- Listing: the pre-change review (`listing.json`, 22:10Z) had T4 NAMED on the literal `X-Real-Ip`
  (`named=1 described=2 general=1`). The re-run after this revision (`listing.json`, 02:45Z) reads
  `FAIL named=0 described=4 general=0`: the NAMED label is gone and the rest are the DESCRIBED
  contract sentences the user already waived (`LISTING_WAIVER.md`). No specific header is named in
  instruction.md.
- No concept was dropped: C1, C2 and C3 remain independent and the reference fix is unchanged.

### Gate (this revision, run 2026-10-25)

- static: PASSED (blind.patch still absent; allowed, wired separately).
- nop: PASSED at 02:35Z — 11/11 security tests failing, 10/10 functional passing on the pinned tree.
- oracle: PASSED at 02:38Z — 3/3 runs at reward 1.0 (`oracle1-1792895753`,
  `oracle2-1792895755`, `oracle3-1792895757`).
- patches: PASSED at 02:52Z — all 12 declared checks behaved as declared (the blind patch is the
  only absent entry and the gate skips it). Eight security/functional-fail shapes plus upstream A
  alone and A+B failing; alternative and hardening fixes at 1.0.
- No test, solution/fix.patch, manifest or checks file was touched, per the audit.

