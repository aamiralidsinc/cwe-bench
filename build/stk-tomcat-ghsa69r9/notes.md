# stk-tomcat-ghsa69r9 build notes

Start (UTC): 2026-10-26T02:17:04Z
End (UTC): pending

## What this is

Apache Tomcat 11.0.19-dev at `81c7afb323cf4f12f8b49a422962ad3588917e9c`, the parent of the earlier advisory fix `6d955cceca84` (CVE-2026-29146, a padding-oracle in the cluster channel's encryption interceptor). The later advisory (CVE-2026-34486, GHSA-69r9-qgr7-g2wj) is a fix of the fix: the earlier change moved message delivery outside the decryption failure handler, so an undecryptable or plaintext frame was forwarded; the later fix `1fab40ccc752` reverts that one line. Pattern H3a: pin = the parent of A; the reference fix = A + B plus fixes for the uncovered routes.

### Note on the build prompt's screener lead

The screener record embedded in the build prompt (Kubernetes/OpenShift membership providers) does **not** match the advisories or the published fix commits. The six fix commits (`0112ed22abfc`, `607ebc0fa522`, `6d955cceca84`, `1fab40ccc752`, `55f3eb914823`, `776e12b3e2b0`) touch only `EncryptInterceptor.java`, its `LocalStrings` and its tests/docs; the `membership/cloud` providers are untouched. The task was therefore built from the actual advisory and fix commits. The on-disk reader record `pipelines/stacking/out/reader/h3-ghsa-69r9-qgr7-g2wj.json` is the EncryptInterceptor record; it marks the candidate not usable with two groups (the default and the opt-in modes collapse under one authentication fix). This build separates the default route (T1) from the opt-in-mode route (T2) only as part of one *concept*, and adds two genuinely independent concepts (malformed frames, producer bypass) so the stack has three independent edit sites. The record used as `stacking.reader_record` is the path the build prompt mandates.

## Levers, one line each

- **T1** (advisory route, type both): the default configuration has no integrity check, so a changed IV or non-final ciphertext bit is delivered. `EncryptInterceptor.java:57`, `:505-517`, `:130-140`.
- **T2** (Pattern B, type both): OFB/CFB are documented opt-ins routed to the same unauthenticated manager, so a default-only fix leaves them open. `EncryptInterceptor.java:338-340`.
- **T3** (Pattern B, type mimo): a frame shorter than the IV throws an unchecked `IllegalArgumentException` instead of being discarded; the localized short-message key already exists but is unused. `EncryptInterceptor.java:505-517`, `:140-146`, `LocalStrings.properties:24`.
- **T4** (Pattern B, type deepseek): a component that originates its own messages below the encryption layer sends them straight to the transport; the startup guard walks only the opposite chain. `EncryptInterceptor.java:86-97`, `TcpPingInterceptor.java:149-160`, `StaticMembershipInterceptor.java:200-235`.

Concepts: `[T1, T2]` (authenticated transport for every supported configuration), `[T4]` (no originator below the protection point), `[T3]` (malformed input is discarded).

## Verified on the pinned tree

- All 7 security cases fail at the pin for the intended reason: the four tamper cases deliver the modified plaintext; the two truncated-frame cases throw `IllegalArgumentException: IV buffer too short for given offset/length combination`; the producer case captures the 64-byte plaintext marker on the wire.
- All 18 functional cases pass at the pin (the project's own `TestEncryptInterceptor`, 16 cases, plus 2 chain cases).
- The reference fix: 25/25. The alternative AEAD-upgrade fix: 25/25. The hardening fix: 25/25.
- Per-concept miss patches: `miss_integrity` leaves only the four tamper cases failing; `miss_producer_guard` leaves only the producer case failing; `miss_short_frame` leaves only the two truncated-frame cases failing. Functional tests pass in all three.
- Recall: upstream A alone fails 6 security cases and A+B fails 7 (A alone forwards the plaintext probe, so the producer case fails there too); functional tests pass in both.
- The full tree compiles offline with Ant 1.10 and JDK 17 from the warmed `/opt/tomcat-deps` (38 s); the project's `TestEncryptInterceptor` runs offline from the pinned test sources.
- Wrong fixes: `default_gcm` (the default-only fix, and the control's reference) fails 5 security cases; `crash_on_failure` fails 6 security cases with functional passing; `verify_only` and `functional_fail` fail 13 functional cases.

## Not verified / unknowns

- The fetched advisory text does not state the exact intended mitigation for CVE-2026-29146. The reference fix therefore makes every non-AEAD mode authenticated rather than only switching the default.
- Current upstream main (`17aa1769`, checked 2026-10-26) has since changed the default to `AES/GCM/NoPadding`, but still has T2 (no MAC on OFB/CFB), T3 (no minimum-length check) and T4 (guard still walks the previous chain only). The register rows therefore say `present_in_latest=yes`.
- The fix-commit list spans three release branches. The check patches use the branch the pin is on: A `6d955cc`, B `1fab40`. The other branches' commits are recorded in the manifest history but are not applied.
- No Kubernetes/cloud-provider code is involved; the screener's Kubernetes traps were not used (see above).

## Gate

- static: PASS on every check except the expected missing `blind` patch (and `FAIRNESS.md`, written later). The only reported problem is `manifest.patch_checks has no expect=pass patch with kind='blind'`.
- nop: **PASSED** (2026-10-26T04:03Z): the pinned tree builds with Ant offline and every one of the 7 security tests fails while all 18 functional tests pass.
- oracle: pending
- patches: pending
- control: pending
