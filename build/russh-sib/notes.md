# russh-sib build notes (sibling task)

## Relationship to the base `russh` task

The base `russh` task is the real upstream flaw: SSH algorithm agreement accepts
`mac=none` paired with a MAC-requiring block cipher (aes*-ctr/cbc, 3des-cbc),
yielding an integrity-free session (the CWE-129 panic is only a downstream
symptom). The upstream fix hardened MAC selection and added a read-path bounds
check.

`russh-sib` keeps that flaw as one sibling and extends the task to the full
*class* of trust decision it belongs to: **the handshake must refuse any
combination that leaves the session without cryptographic protection.** This is
`mined+injected` — the injected part is widening the hidden test suite to cover
same-class acceptance gaps the upstream fix did not touch, not inventing new
source-level flaws. All gaps are genuine, pre-existing code paths in russh.

## Multi-sink verification (the thing that decides whether this task is valid)

Three independent acceptance gaps, at three distinct stages of the shared
handshake routine, each reproducing on the vulnerable commit through the real
public client/server transport API over loopback:

1. **KEX stage — null key exchange.** `kex::NONE` (the only algorithm whose
   `skip_exchange()` is true) is registered and selectable. When chosen, both
   client and server skip the DH exchange and jump straight to NEWKEYS with
   `server_host_key = None` and an empty exchange hash: no key agreement, no
   host-key signature, no authentication. NOT touched by the upstream fix.

2. **CIPHER stage — null cipher.** `cipher::NONE` and `cipher::CLEAR` both map to
   the `Clear` cipher (`key_len 0`, `tag_len 0`, `needs_mac()==false`). Paired
   with `mac=none` the handshake completes with plaintext and no integrity. NOT
   touched by the upstream fix: because `needs_mac()` is false for `Clear`, the
   upstream `mac=none` refusal never fires for it.

3. **MAC stage — block cipher + null MAC.** The base flaw. COVERED by the
   upstream fix.

A single one-line check cannot close all three: they sit at different stages
with different conditions (null KEX is about `skip_exchange`; null cipher is
about a non-AEAD cipher with no MAC; block+none is about `needs_mac`). A correct
fix must guard each. This is genuinely multi-sink — the opposite of the
single-sink shape that caused async-sib to be abandoned.

### Candidate dimensions that were checked and REJECTED
- **Weak/downgraded KEX** (group1-sha1 etc.): selecting a weak-but-real KEX still
  performs real key agreement and signs the host key, so the session keeps
  integrity/authentication. Ordinary preference-list policy, not a null-acceptance
  bug — not the same class.
- **Host-key algorithm downgrade**: host-key selection always ends on a real,
  signed key; there is no null host key. Signature-strength policy, different
  class.
- **Compression=none**: the default, entirely safe; not a weakness.
- **Client vs server direction**: `Client::select`/`Server::select` are separate
  implementations, so each sink is exercised in both directions as *variants*;
  but a fix in the shared routine closes both directions, so direction adds test
  coverage, not a distinct fix site.

## Tests

- Security (7): null-kex (client/server offered), null-cipher `none`+mac=none
  (client/server offered), `clear`+mac=none, aes256-ctr+mac=none (base),
  aes256-cbc+mac=none (base variant). Each asserts the handshake does NOT
  connect.
- Functional (7): default handshake; aes256-ctr+hmac-256; aes256-cbc+hmac-512;
  aes256-gcm+none (AEAD, legit); chacha20-poly1305+none (AEAD, legit); full echo
  round-trip over curve25519+aes256-ctr+hmac; a second real kex
  (mlkem768x25519-sha256) connects.

## Oracle and wrong-fix patches

- `solution/fix.patch` (oracle): edits only the shared handshake routine —
  refuse the null KEX, and require a genuine MAC whenever the cipher is not AEAD
  (covers both block ciphers and the null/clear cipher; AEAD stays allowed with
  mac=none).
- `checks/base_fix_only.patch` = the real upstream fix (MAC refusal + bounds
  check). Expect **security_fail**: closes the two block-cipher tests, leaves all
  null-kex and null-cipher tests failing; functional all pass.
- `checks/partial_fix.patch` = upstream MAC fix + a null-KEX guard. Expect
  **security_fail**: still leaves the null-cipher tests failing (two of three
  sinks fixed is not enough).
- `checks/disable_feature.patch` = ban mac=none for every cipher. Expect
  **functional_fail**: breaks the legitimate AEAD+none functional tests.
- `checks/alt_correct_fix.patch` = same property enforced with one consolidated
  post-selection integrity check (different shape). Expect **pass** (1.0).

## Build / runtime

Reuses the base `russh` environment verbatim (harness crate at /opt/harness,
path dep on /app/russh, ring backend, cargo-nextest JUnit, fully offline, the
only peer is an in-process loopback socket). Rust compiles are slow and the base
image is not cached; the dependency layer is pre-compiled so an agent edit to
/app/russh recompiles only russh.

## Gate result

`python3 -I builder/gate.py russh-sib` printed **PASSED** (exit 0) on
2026-10-14. Stages:
- static: ok (no leaks; source=mined+injected; all four check patches present).
- nop (vulnerable code): 7 security tests, all FAIL; 7 functional tests, all
  PASS.
- oracle: reward 1.0 on both runs, identical results.
- patches:
  - base_fix_only.patch -> security_fail (reward 0.2857; 5 security failing:
    both null-kex, both null-cipher, clear-cipher; functional all pass).
  - partial_fix.patch -> security_fail (reward 0.5714; 3 security failing: both
    null-cipher, clear-cipher; functional all pass).
  - disable_feature.patch -> functional_fail (3 functional failing: the two
    AEAD+none tests and the mlkem handshake which uses aes256-gcm+none).
  - alt_correct_fix.patch -> pass (reward 1.0).

Report at build/russh-sib/gate_report.json.

### Note on nextest fail-fast
tests/test.sh adds `--no-fail-fast` to both nextest invocations (the only edit
to the template command lines). Without it, nextest cancels remaining tests
after the first failure, so on vulnerable code the JUnit could contain fewer
than all 7 security cases (the fragility the base russh notes flagged). With
`--no-fail-fast` all 14 cases appear in every run, so the counts are
deterministic.

## 2026-10-16 test repair

Inputs: lenient_items_2026-10-16.txt (three `-- REC russh-sib` items), the audits' verdict.json
under `~/.tb-graders/cwe/jobs/russh-sib-*/*/postmortem-*/`, and the coordinator's extra items
(the missing no-MAC and re-key cases, and the null-cipher-with-MAC ambiguity).

### Items and decisions
| item (source) | decision |
|---|---|
| One-role fix passes: both peers ran the patched library, so a fix in only the client or only the server role still passed (r1-n002 audit) | **fixed.** The new `legacy_*` security tests put the library under test on ONE side. The attacker is `russh_peer`, which is russh at the vulnerable commit renamed to its own crate (`tests/peer/russh-peer.tar.gz`, built by `build/russh-sib/make_peer.py`; `test.sh` unpacks it to /opt/russh-peer and adds it as a harness dependency). There are 4 server-under-test cases (null kex, null cipher, aes128-ctr and 3des-cbc with mac=none) and 4 client-under-test cases (null kex, clear cipher, aes128-cbc and aes192-ctr with mac=none). The client's own handshake result does not show what the server decided: with the null exchange, russh's client calls itself done before the server answers. So server acceptance is read from the wire. A relay watches the plaintext server-to-client stream, and the attack counts as successful once the server sends NEWKEYS. Fair: the instruction says "in either direction", and a malicious peer does not run the fixed library. |
| No-MAC variants beyond aes256 (r11 audit; coordinator) | **fixed.** Added 3des-cbc (both-sides test, server-offered), plus aes128-ctr, aes128-cbc, 3des-cbc and aes192-ctr in the legacy tests. All are stated in the instruction ("the CTR and CBC family, and triple-DES"). |
| Null kex at re-key (r11 audit; coordinator) | **fixed (one direction).** `legacy_server_rekey_to_null_kex_refused_by_client`: a real initial exchange and a working session; then the client re-keys and the peer answers offering only `none`. Success for the attacker = the client under test completes a second key exchange (its own kex_done). Fair: "a handshake that would settle on the null key exchange must be rejected", and a re-key is a key-exchange handshake. A server-side re-key security test was **skipped**. Server acceptance cannot be observed reliably there: the re-key traffic is encrypted, and russh's client switches keys before the server's NEWKEYS, so the attacker's own record is unreliable. Two functional tests were added so that refusing all re-keys is not a fix: `rekey_with_real_kex_keeps_session_{server,client}_side`, where a real re-key completes and data still round-trips. Also added `legacy_{client,server}_default_interoperates`. |
| Null cipher with a genuine MAC: the instruction pointed both ways (r11 audit; coordinator) | **resolved.** No test depends on it (none did before either). The instruction now says (one sentence added, one word changed): "Any encrypting cipher paired with a genuine MAC must continue to connect and carry data. Whether the no-encryption cipher may still be used with a genuine MAC is left to you; either choice is accepted." |
| A hang or panic passes as a refusal (mimo kDawEPf audit) | **fixed.** Every security test now uses `assert_refused`: not connected, the attempt ended in an error before the 20 s limit (not a timeout), and no panic anywhere in the process (a panic hook counts them). Fair: "must be rejected cleanly as a failed handshake". |
| Missing final-code/changes.patch in postmortem bundles | not a test item; out of scope. |

`test.sh` now builds first, with retries (`-j 2, 2, 1`) and logs to /logs/verifier/build.log.
Each group's nextest output goes to `<group>/nextest.log`. One gate oracle run lost its security
group when its compile failed during the Colima disk-full window (05:45-06:00 UTC). That was an
infra failure, and the gate was rerun.

Tests are now 17 security (was 7) and 11 functional (was 7).

### New patch checks (all in manifest)
- `client_role_only.patch`: correct checks in client/kex.rs only. Result: security_fail (the 4 `legacy_client_*` tests).
- `server_role_only.patch`: correct checks in server/kex.rs only. Result: security_fail (the 5 `legacy_server_*` tests, plus both null_kex tests, where the client role completes a null exchange).
- `initial_kex_only.patch`: the reference fix, but the null kex is refused only when not re-keying. Result: security_fail (the re-key test).
- `named_ciphers_only.patch`: the reference fix, but a MAC is required only for aes256-ctr/cbc and the null cipher. Result: security_fail (the 3des, aes128 and aes192 tests).
- `panic_refusal.patch`: the reference logic, but it refuses with a panic. Result: security_fail (all 17).
- `refuse_rekey.patch`: the reference fix plus refusing every re-key. Result: functional_fail (both re-key functional tests).
- `blind_deepseek_r11.patch` (kind `blind`): the saved final code of trial deepseek-r11 LZmNT5B (no network; it saw only the instruction and the repo). Result: pass, 1.0.
Existing checks are unchanged and still behave as expected: base_fix_only security_fail, partial_fix security_fail, disable_feature functional_fail, alt_correct_fix pass. The remaining static warning: no `hardening`-kind patch (a warning only, since the task predates strict_gate).

Locally, four model fixes rebuilt by replaying the Edit/Write calls in the transcripts also score 28/28:
deepseek-r1 36yhNx9, deepseek-r1 u7jtLQY, mimo GCJoz2Q and mimo kDawEPf.
These trials have no final-code, so this is informational only. The local runs used Rust 1.91.1 on macOS.

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py russh-sib` printed **PASSED** on 2026-10-16
(nop: 17/17 security fail and 11/11 functional pass; oracle 1.0 twice; all 11 patch checks as expected).

### Regrade
No test was relaxed. The regrade criterion is: current reward 1.0 and saved `final-code/changes.patch`. Only one trial meets it.

| trial | old | new | failing tests |
|---|---|---|---|
| russh-sib-deepseek-r11-20261015-221248-n001 / LZmNT5B | 1.0 | 1.0 (regrade-20261016T072318Z: 17/17 security, 11/11 functional, real build) | none |

The other 1.0 trials have no final-code: deepseek-r1 36yhNx9, deepseek-r1 u7jtLQY, mimo GCJoz2Q and mimo kDawEPf.
They cannot be regraded with regrade_from_code.py. Their fixes, rebuilt from the transcripts, pass the repaired tests locally (see above).
fAth3gU and y7Fbccp have no reward and no final code.
