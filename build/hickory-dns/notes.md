# hickory-dns build notes

## Verified against the code (not trusted from the candidate row)

- **Flaw.** `CachingClient::lookup` in `crates/resolver/src/caching_client.rs`
  computes `is_dnssec = client.client.is_verifying_dnssec()` but, on the
  vulnerable parent commit, never consults the per-record DNSSEC verdict before
  returning. Records that validation marked `Proof::Bogus` are returned to the
  caller inside `Ok(Lookup{..})`. Reproduced directly: on the vulnerable commit
  both `Resolver::lookup` and `Resolver::lookup_ip` return
  `Ok(.. proof: Bogus ..)`; on the fix commit they return an error.

- **Trust decision / entry points.** `Resolver::lookup` routes through
  `inner_lookup` -> `LookupFuture`; `Resolver::lookup_ip` routes through
  `LookupIpFuture` directly. Both converge on `CachingClient::lookup`, which is
  where the upstream fix places the check. Confirmed `lookup_ip` does not call
  the public `lookup`, so a one-site fix inside `lookup` leaves `lookup_ip`
  exploitable — this is the basis of the `security_fail` check.

- **Tempting wrong fix (candidate's claim), verified.** Candidate said a fix in
  `Resolver::lookup` that rejects non-secure records (a) misses `lookup_ip` and
  (b) would break unsigned/insecure zones. Both confirmed:
  - `shallow_poc_only.patch` adds the check only in `Resolver::lookup`; the two
    `lookup_ip` security tests still fail while all functional tests pass.
  - `disable_feature.patch` rejects anything not fully `Secure` regardless of
    whether validation was requested; unsigned (validation-off) answers carry
    `Proof::Indeterminate`, so four functional lookups break.
  - `alt_correct_fix.patch` places the Bogus check at the resolver layer in
    BOTH `lookup` and `lookup_ip`; all 9 tests pass (a valid alternate fix at a
    different layer than upstream).

## No-network design

- The `test-support` crate's `MockProvider`/`MockNetworkHandler`/`MockRecord`
  (present at the vulnerable commit) provide a fully in-process scripted
  upstream. No sockets, no real DNS. This mirrors the upstream fix commit's own
  added unit test.
- `Proof::Bogus` is produced deterministically by giving the validating resolver
  a trust anchor while the scripted upstream denies the DS RRsets with unsigned
  SOA records, so no chain of trust can be built.

## Could NOT verify / guesses

- The crate's own DNSSEC resolver tests query live public resolvers, so they
  were not run in the no-network image (documented in the manifest).
- The upstream fix also touches the server forwarder (`catalog.rs`) and the
  retry handle; those are included in `fix.patch` for fidelity but are not
  exercised by the harness (the harness uses the resolver library API, not the
  server crate). The variants cover the resolver-side entry points, which is the
  documented library entry point for this task.
- Base image is `rust:1-slim-bookworm` (latest stable). The shipped `Cargo.lock`
  was resolved with stable 1.99; the image toolchain must be >= the MSRVs it
  pins (max observed 1.90). Latest stable satisfies this.

## Host validation (outside Docker, for fast iteration)

All four states were run with `cargo nextest` against the real repo at the two
commits and with each check patch applied:
vulnerable -> 4 security FAIL / 5 functional PASS; oracle -> 9 PASS;
shallow -> 2 security FAIL, functional PASS; disable -> 4 functional FAIL;
alt -> 9 PASS. The gate re-runs all of this inside Docker.

## 2026-10-16 test repair

Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Flagged items from
`build/audit/lenient_items_2026-10-16.txt` / `research/own-runs/TEST-REPAIRS.md` plus notes.

### Items and decisions
| # | Item | Decision |
|---|------|----------|
| 1 | functional tests use only non-validating resolvers, so "fail every validating lookup" scores 1.0 (pJXHdmD, DMUx8ae, K6AyPff) | **fixed**: 6 new functional tests on a validating resolver over a correctly signed tree built in the test (root anchor -> signed DS -> `testing.`): Secure A via `lookup`, Secure via `lookup_ip`, Secure TXT, Secure CNAME chain via `lookup_ip`, Insecure (signed-NSEC-proven unsigned delegation) A via `lookup` and via `lookup_ip`. Each asserts the expected address. Follows from "lookups that are legitimately resolvable must continue to return their answers". |
| 2 | security tests accept any error (K6AyPff rec b) | **fixed** + one instruction sentence: every security test now uses `assert_validation_failure`: error must not be a no-records / NXDOMAIN negative answer and not Timeout / NoConnections / Busy / Io. No error type or message is required. |
| 3 | add a Bogus-CNAME variant whose target needs a separate query (K6AyPff rec c) | **fixed**: `lookup_forged_cname_is_rejected`, `lookup_ip_forged_cname_is_rejected`: signed zone serves `login.signed.testing. CNAME evil.unsigned.testing.` with an RRSIG made over a different target; the target (A and AAAA) lives in the proven-unsigned zone (legitimately Insecure). Also added `lookup_a_tampered_signature_is_rejected` (intact chain, data altered after signing; the instruction names "tampered" signatures). Note: the audit's guess that an Exists-arm-only check misses the CNAME chain is wrong (preserved CNAMEs flow into the inner Exists answer); `exists_arm_only.patch` passes and is kept as a `pass` check. The CNAME tests instead bite a check that only judges records of the requested type. |
| 4 | Bogus NSEC negative response (K6AyPff rec c, "possibly") | **skip**: negative answers already return an error on the vulnerable code; the instruction only promises failure for answers handed to the caller as success. |
| 5 | grader should clean/isolate /opt/target (pJXHdmD rec) | **fixed** in `tests/test.sh`: harness assembled in a fresh `mktemp` dir (manifest written by test.sh, nextest config written by test.sh, tests from /tests), fresh `CARGO_TARGET_DIR` and fresh `CARGO_HOME`; crate archives copied only if their sha256 matches the lockfile; lockfile taken from /opt/harness only if its sha256 matches the pinned value (else no build, reward 0); `/.cargo` and `/tmp/.cargo` removed; RUSTFLAGS/RUSTC_WRAPPER/CARGO_TARGET_*/NEXTEST_* unset. The tree is removed by an EXIT trap after scoring. Cold build ~45-75 s. Checked: planted `/.cargo/config.toml` + `/opt/cargo/config.toml` (runner=/bin/true) and a replaced `/opt/harness/tests/security.rs` are ignored (vulnerable still 0/7 security). Residual: /app/tests/test-support (the repo's mock crate) and the toolchain itself are still agent-writable. |
| - | postmortem bundle should include final-code (K6AyPff rec) | out of scope (postmortem tooling). |

Instruction change (one sentence, appended to the first "must guarantee" bullet):
"The error must be recognisable as a validation failure, not reported as an ordinary negative
answer (the name or record does not exist) or as a network failure or timeout."

Shared fixture: `tests/common/signed_zone.rs` (copied to the harness as `tests/common/mod.rs`).
Own `MockHandler` implementation; keys generated per run; all expected values computed in the test.

### Patch checks (dev container runs, new test.sh)
| patch | expect | result |
|---|---|---|
| (vulnerable) | - | sec 0/7, fun 11/11 |
| reference fix | pass | 7/7, 11/11, 1.0 |
| shallow_poc_only | security_fail | sec 4/7 (3 lookup_ip) |
| disable_feature | functional_fail | fun 5/11 |
| alt_correct_fix | pass | 1.0 |
| reject_all_validating (new) | functional_fail | fun 5/11 (all 6 validating) |
| require_secure_when_validating (new) | functional_fail | fun 9/11 (2 Insecure) |
| bogus_as_no_records (new) | security_fail | sec 0/7 |
| query_type_only (new) | security_fail | sec 5/7 (2 forged CNAME) |
| exists_arm_only (new) | pass | 1.0 |
| DMUx8ae saved final code | - | 1.0 |

The `shallow_poc_only` result above is from the gate (sec 4/7: two `lookup_ip_bogus` cases plus
`lookup_ip_forged_cname`), after the forged-CNAME target got an AAAA record.

Also during the repair, the forged-CNAME target first had no AAAA. With that setup,
`lookup_ip_forged_cname` failed `exists_arm_only` and `disable_feature` with a NoRecords error,
because `lookup_ip` merged the A-leg validation error with the AAAA-leg "no AAAA" result.
That edge comes from how lookup_ip merges its legs, not from the property under test, so the
target now has both A and AAAA (unsigned, Insecure).

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py hickory-dns` -> **PASSED** (nop sec 7 / fun 11
failing as expected, oracle x2 = 1.0, all 8 patch checks as expected). Warnings only: no
`hardening` / `blind` pass patches (pre-2026-10-16 task, not strict).

### Regrade
| trial | old | new | failing tests |
|---|---|---|---|
| hickory-dns-deepseek-r11-20261015-215342-n001/hickory-dns__DMUx8ae | 1.0 | 1.0 (`regrade-20261016T071435Z`) | none |

Not regradable (no `final-code/changes.patch` saved): pJXHdmD (deepseek r1; byte-identical to
the upstream fix per its audit, so it is expected to pass), K6AyPff (mimo r1),
5Wxrxmv (deepseek seq1). No test was relaxed, so runs below 1.0 were not regraded (there are none).
