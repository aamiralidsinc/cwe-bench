# russh task build notes

## What the flaw really is (verified against the fix commit, not the CWE label)

The candidate is labelled CWE-129 (improper array-index validation) and the
public panic is an out-of-bounds slice in the packet read path. That label is
misleading, as the reader warned. Reading the fix commit
(`2885385`) the substantive change is in SSH **algorithm negotiation**:

- Vulnerable: MAC selection took the selected algorithm whenever selection
  succeeded, and only consulted whether the cipher *needs* a MAC in the
  no-common-MAC *fallback* branch. So if both peers listed `none` for the MAC
  while the cipher was a MAC-requiring one (aes*-ctr/cbc, 3des-cbc), `none` was
  accepted and a session with `tag_len()==0` — i.e. **no integrity protection**
  — was established.
- The panic is a *downstream symptom*: once such a session exists, a short
  packet drives `buffer.buffer[l..]` out of bounds.

The fix has two parts: (1) negotiation refuses `mac=none` whenever the cipher
needs a MAC, regardless of how the pairing arose — the real root cause; (2) a
bounds check in the read path as defense-in-depth against the panic.

## Why the tests are shaped this way

- The **tempting wrong fix** is "just add the bounds check so it stops
  panicking" (candidate's `tempting_wrong_fix_JUDGEMENT`). That is
  `checks/shallow_bounds_check_only.patch`. It leaves an integrity-free session
  fully negotiable, so every security test (which asserts the session is
  *refused*) still fails under it.
- Security tests therefore assert on the *negotiation* outcome (the session
  must not be established), not on the panic. They go through russh's real
  public transport API over loopback: a peer offering a MAC-requiring cipher +
  `mac=none` must fail to connect.
- Variants cover CTR (aes256/aes128), CBC (aes256), 3des-cbc, and both
  directions (attacker-as-client vs attacker-as-server).
- Functional tests keep legitimate combinations working, crucially including
  AEAD ciphers (chacha20-poly1305, aes256-gcm) with `mac=none`, which is valid
  because AEAD provides its own integrity. This is what catches the overbroad
  "ban none everywhere" fix.

## Could not / did not verify

- The raw out-of-bounds panic itself is NOT exercised by a test: triggering it
  requires driving a crafted short *encrypted* packet after KEX, which a real
  russh peer never sends, and reaching it needs the vulnerable negotiation
  anyway. Testing the negotiation refusal is both sufficient and the correct
  discriminator (the panic-only fix must fail), so the panic path is left to
  the defense-in-depth part of the reference fix.
- `needs_mac()` and the negotiation internals are `pub(crate)`, so tests cannot
  call them directly; everything is observed through the public API, as
  required.

## Gate result

`python3 -I builder/gate.py russh` printed **PASSED** (exit 0). Stages: static
ok; nop (security tests fail, functional pass on vulnerable code); oracle 1.0
twice, identically; patches: shallow_bounds_check_only -> security_fail,
overbroad_ban_none -> functional_fail, alt_correct_fix -> pass.

Note on the security-test count: the source defines 5 security tests (the 3des
variant included) and two independent clean image builds run all 5. During the
gate's own Harbor build the image happened to bake a stale harness layer and the
nop/patch stages observed only 4 security tests (the 3des one absent). The gate
still PASSED (4 >= the minimum of 4, and every patch discriminated correctly).
A fresh build of `environment/` reliably yields 5, so a real trial, which
rebuilds the image, runs all 5.

## Build / runtime

- Rust. Scratch clones and cargo target dirs were kept under
  `~/.tb-graders/cwe/work/russh/`, never inside `cwe-bench/`.
- The harness crate is baked into the image at `/opt/harness` (a path
  dependency on `/app/russh`), dependencies pre-compiled in a cache layer so an
  agent edit to `/app/russh` recompiles only russh. `cargo-nextest` emits JUnit
  XML per group. Runtime is fully offline; the only peer is a loopback TCP
  socket spun up in-process by the test.
- The harness pins russh to the `ring` crypto backend to keep the offline
  compile light; the backend does not affect the negotiation logic under test.

## 2026-10-16 test repair

Flagged items (lenient_items_2026-10-16.txt, TEST-REPAIRS.md `## russh`) and decisions:

| # | Item | Decision |
|---|------|----------|
| 1 | REC russh-deepseek-1013-221533 / r11: the security tests accept *any* failure to connect (a crash, a hang until the 20 s timeout, any handshake error). Assert a negotiation error instead. | **fixed.** `negotiate()` now records a client-side timeout, the client error, and whether the client's or the server's connection task panicked (`russh::Error::Join` / `JoinError::is_panic`). The five peer-to-peer tests use `assert_refused`: no session, no timeout, no panic, an error returned. The new raw-peer tests (item 2) go further: the raw peer follows the protocol and never hangs up first, and the same raw peer with a real MAC (or an AEAD cipher) connects in functional controls. So when the library returns an error there, the error is its own refusal of the cipher/MAC pairing. No error variant is required: `NoCommonAlgo` is the upstream design, and the instruction asks only for "rejected ... cleanly, as a failed negotiation". |
| 2 | == russh-mimo-1013-221533 (lenient-test) + REC: both peers run the patched library, so a fix in one role only (server-side or client-side negotiation) still passes every directional test. Add a raw/unpatched KEXINIT peer. | **fixed.** New `raw` module in `tests/harness/src/lib.rs`: a raw SSH transport peer that sends its own KEXINIT (test-chosen cipher and per-direction MAC lists) and completes a genuine curve25519-sha256 exchange. X25519 is in-file (RFC 7748 ladder); SHA-256 comes from `ssh_key::HashAlg`, the Ed25519 host-key signature from `ssh_key`'s `Signer`; there are no new crates and no product internals. The raw client never hangs up first, so a server that keeps serving after both NEWKEYS counts as Established. The raw server holds the socket until the client leaves, and the verdict is `client::connect`'s result. 7 new security tests: library as server against a raw client (aes256-ctr+none, aes256-cbc+none, none only server->client, none only client->server) and library as client against a raw server (aes256-ctr+none, 3des-cbc+none, aes128-ctr with none only server->client). 4 new functional controls: the raw client with aes256-ctr+hmac-sha2-256 and with chacha20-poly1305+none is served; the raw server with aes256-ctr+hmac and with aes256-gcm+none is accepted. All use the permissive operator config that lists `none`. |
| 3 | REC russh-mimo (3): agent limit 3600 s vs task.toml 7200 s; changes.patch not captured; disk full | **skip.** Harness/infra, not tests. |
| 4 | (found while gating) `nextest` ran with its default fail-fast, so on a failing run it cancelled the remaining tests and the JUnit listed only about 4 security tests. This is the "4 security tests / stale layer" seen in the original gate. It distorted partial rewards (a reward of 1.0 was unaffected). | **fixed.** `tests/test.sh` passes `--no-fail-fast` to both nextest runs. The nop stage now sees all 12 security and 10 functional tests. |

The instruction is unchanged. "In either direction of the exchange", "never finish bringing up a session that pairs a cipher requiring a separate integrity MAC with the null MAC" and "rejected ... cleanly, as a failed negotiation" already state every new property.

New patch checks (all in `manifest.json`):
- `server_role_only_fix.patch` (security_fail): the check sits only after `Server::read_kex` in server/kex.rs. Passed all 5 old security tests; now fails the 3 raw-server (library-as-client) tests, reward 0.75.
- `client_role_only_fix.patch` (security_fail): the check sits only after `Client::read_kex`. Passed all old tests; now fails the 4 raw-client tests, reward 0.667.
- `panic_instead_of_refusal.patch` (security_fail): the negotiation panics instead of returning an error. Passed all old tests (a panicked task means "not connected"); now fails all 12.
- `one_direction_mac_check.patch` (security_fail): refuses only when the client->server MAC is none. Passed all old tests; now fails the 2 server->client-only tests.

Local check (host cargo, vulnerable source plus each patch): the reference, alt_correct_fix and the deepseek-r11 saved final code pass 12/12 security and 10/10 functional. The vulnerable code fails all 12 security tests and passes all 10 functional ones.

Gate: `python3 build/slot.py 3 -- python3 -I builder/gate.py russh` -> **PASSED**. Static ok; nop has 12 security and 10 functional tests; oracle 1.0 twice. Patch checks: shallow 0.0 (12 sec fail), overbroad 0.0 (4 functional fail), alt 1.0, server-role-only 0.75, client-role-only 0.667, panic 0.0, one-direction 0.833. The first gate attempt failed at the patch stage with a Docker compose error during the Colima disk-full window. That was infra and was re-run.

Regrade (`build/regrade_from_code.py`; only trials with `final-code/changes.patch` can be regraded):

| trial | old | new | failing tests |
|-------|-----|-----|---------------|
| russh-deepseek-r11-20261015-220545-n001/russh__aYJsEe9 | 1.0 | 1.0 (regrade-20261016T072117Z, 12 sec + 10 func ran) | none |
| russh-deepseek-1013-221533/russh__6zvdBLF, russh__rN2yCVN | 1.0 | not regradable (no final-code saved) | - |
| russh-mimo-1013-221533/russh__t2scdx3, russh__v894G6B | 1.0 | not regradable (no final-code saved) | - |

The audit describes the t2scdx3 (mimo) fix as a change to the shared `Select::read_kex` default, which serves both roles. On that description it would pass the raw-peer tests too, but this could not be confirmed without saved code.
