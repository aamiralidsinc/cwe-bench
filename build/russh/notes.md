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
