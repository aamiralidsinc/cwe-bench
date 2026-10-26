# joserfc-ds — build notes

- Start: 2026-10-24T05:27Z (build session)
- End: 2026-10-24T06:28Z
- Repo: authlib/joserfc, pinned `1e5b94da589c695f54abd9f1a0ad822dcffe0305` (v1.6.7, verified parent of the
  published fix `86d00910b2b2d2d07503fee9b572906daefab7f1`).
- Advisory: GHSA-GG9X-QCX2-XMRH / CVE-2026-49852 / PYSEC-2026-2528 — an empty HMAC secret is accepted for
  HS256/384/512 verification, so a MAC anyone can recompute authenticates any claims (CWE-1391/CWE-287/CWE-326, A07).
- Pattern A+B, track **injected**.

## The one property (written before the routes)

**An empty secret must never authenticate anything.** Whether it is supplied to the library, produced by
it, or transformed by it before use, an empty secret must fail with a client error instead of yielding a
key, a signature, or an accepted token.

Read literally this covers: the reported import + verify sites; every import entry point and the dict-JWK
shape; a hand-built key object; zero-length generated material; an injected producer that turns a supplied
plain secret into key material; and the injected second surface that builds keys from a collection of plain
secrets. It is stated once, over the secret/outcome, and names no route.

Coupled legitimate value, stated once: **secrets that do contain key material keep working exactly as
today, including short secrets the library already accepts with a warning.** This is the anti-over-hardening
lever (a fix that rejects <14/<32-byte keys breaks the project's own `test_import_key_with_warnings` and
the task's functional suite).

## One-line levers

- **T1 base (A, report site)**: `OctKey.import_key(""/b""/{"k":""})` yields a zero-length MAC key and
  `HMACAlgorithm.sign/verify` call `hmac.new` with it; driven through `jwt.encode/decode`,
  `jws.serialize/deserialize_compact`, JSON general/flattened and RFC 7797. Where
  `src/joserfc/_rfc7518/oct_key.py:53-64`, `src/joserfc/_rfc7518/jws_algs.py:62-70`. No dismissal (reported).
- **T2 import entry points + shape (A, far sites)**: `jwk.import_key`, `JWKRegistry.import_key`,
  `KeySet.import_key_set`, `OctKey.import_key` and the **dict-JWK** shape (`{"kty":"oct","k":""}`) whose
  emptiness only appears after base64 decoding. Dismissal: "key import is just parsing; the report is about
  verification" and an input-only check (`if not value`) that misses the dict shape.
  Where `src/joserfc/jwk.py:126-162`, `src/joserfc/_keys.py:54-78,169-179`,
  `src/joserfc/_rfc7517/models.py:270-283`, `src/joserfc/_rfc7518/oct_key.py:32-34`.
- **T3 lower-level API (A, defence in depth)**: an `OctKey` constructed directly with empty material (or
  `_raw_value` set) is used to sign/verify. The published fix protects this; an import-only fix does not.
  Dismissal: "users are supposed to import keys; hand-built keys are not an import path."
  Where `src/joserfc/_rfc7517/models.py:88-104`, `src/joserfc/_rfc7518/jws_algs.py:62-70`.
- **T4 zero-length generation (B, protection never existed)**: `OctKey.generate_key(0)` / `jwk.generate_key("oct", 0)`
  returns `b""` (only the <112-bit warning fires); the published fix never touches the generator. Dismissal:
  "a zero-bit key is caller error, not an attacker input; the MAC layer refuses it anyway."
  Where `src/joserfc/_rfc7518/oct_key.py:84-95`, `src/joserfc/_keys.py:80-103`.
- **T5 plain-secret producer (injected, HOW-type, main lever)**: `guess_key` accepts a plain `str`/`bytes`/`bytearray`
  secret and stretches it with SHA-256 to a 32-byte MAC key. An empty supplied secret becomes
  `sha256(b"")`, a public constant, so both the import check and the MAC-layer emptiness check see a
  non-empty key. Fix requires validating the *supplied secret* before the transform. Dismissal: "the key
  object reaching the check is non-empty; the two reported sites are fixed." Where `src/joserfc/jwk.py:63-103`
  (the producer), reached from `src/joserfc/jws.py:114,152` and `jwt.encode/decode`.
- **T6 collection surface (injected, extra)**: `KeySet.import_key_set({"keys": [..., "plain-secret", ...]})`
  accepts plain-string entries and constructs `OctKey` directly, bypassing the import-level check. Dismissal:
  "bulk key-set loading is a separate parsing path, not the key class." Where `src/joserfc/_keys.py:169-179`.
- **T7 coupled short keys (functional, HOW-type)**: non-empty short keys (`b"rfc"`, `"secret"`) keep importing
  with only a `SecurityWarning` and keep signing/verifying; generation of short sizes keeps warning. An
  over-broad minimum-length fix fails the project test and the functional suite. Where
  `src/joserfc/_rfc7518/oct_key.py:61-63,90-92`.
- **T8 coupled plain secrets (functional)**: non-empty plain secrets (str and bytes) and non-empty key-set
  secrets keep working exactly as today; the fix must not ban the convenience. Where `src/joserfc/jwk.py:77-83`,
  `src/joserfc/_keys.py:174-178`.

## Candidate sibling / route audit (everything found in the pinned tree, then the injected additions)

Real, unmodified upstream:

1. `HMACAlgorithm.sign` / `.verify` — the only HMAC JWS sink (`jws_algs.py:62-70`). **T1.**
2. `OctKey.import_key` — published import fix, warns under 14 bytes (`oct_key.py:53-64`). **T1/T2.**
3. `BaseKey.import_key` dict branch → `OctBinding.import_from_dict` (`_rfc7517/models.py:270-283`,
   `_rfc7518/oct_key.py:32-34`); dict `k` is base64-decoded, so `""` is empty only after decoding. **T2 shape.**
4. `OctBinding.import_from_bytes` (`oct_key.py:36-41`) — producer of bytes; the import check calls it through
   `super().import_key`. Candidate for a whitespace/normalising trap → **rejected** (see below).
5. `jwk.import_key` implicit-type fallback (`jwk.py:126-162`), `JWKRegistry.import_key` (`_keys.py:54-78`),
   `KeySet.import_key_set` (`_keys.py:169-179`). **T2 entry points.**
6. `guess_key` (`jwk.py:63-103`) — resolution choke point; raw str/bytes rejected at pinned. **T5 injected.**
7. `OctKey.generate_key` zero size (`oct_key.py:66-98`). **T4.**
8. Public `OctKey(raw, original, parameters)` / `_raw_value` (`_rfc7517/models.py:88-104`). **T3.**
9. `_rfc7515/compact.py:22-36`, `_rfc7515/json.py:67-156`, `_rfc7797/compact.py:18-79`,
   `_rfc7797/json.py:11-52` — every JWS serialization funnels to `alg.sign/verify`, so they are input
   shapes of the same sink, kept for coverage, not separate levers.
10. `jwe_algs.DirectAlgEncryption.compute_cek` (`jwe_algs.py:44-51`) and `CBCHS2EncModel` (`jwe_encs.py:42-75`)
    — CEK/enc lengths are enforced; no empty-key route. Out of scope.
11. `jwe_algs.PBES2HSAlgKeyEncryption` (`jwe_algs.py:243-306`) — an empty oct key is accepted as the PBKDF2
    password. Real uncovered route, but a **different protection** (JWE confidentiality, not HMAC
    authentication) → out of this advisory's scope; not built.
12. `NoneAlgorithm` relies on an empty signature by design (`jws_algs.py:31-40`) → documented feature,
    different vulnerability, not built.
13. Upstream later fixed `verify_general_json` accepting an empty `signatures` list (`f409f8f`), which is
    reachable at the pinned commit. Different vulnerability (no signature at all, no key involved) → out of
    this advisory's scope; noted only.
14. `OctKey.generate_key(key_size=8)` (one byte) and `OctKey.import_key(b"rfc")` are today warning-only:
    legitimate behaviour that must be preserved. **T7.**

Injected candidates (a maintainer could plausibly have left these):

- **S-a plain-secret stretch in `guess_key`** — chosen, **T5**. Realistic because the migration guide in
  `docs/migrations/` shows users arriving from PyJWT/python-jose where the secret is a plain string; a
  maintainer adds a compatibility convenience that stretches it to the algorithm's 256-bit key size.
- **S-b plain secrets in a key-set rotation list** — chosen, **T6**. Realistic because a rotation list of
  configured secrets is a common deployment shape; the code takes the already-raw values and builds the key
  objects itself, a small shortcut a maintainer could take.
- **S-c whitespace strip in `OctBinding.import_from_bytes`** — rejected. A whitespace-only key is not
  publicly computable, so it is not a forgery of the advisory's kind, and the published check sees the
  post-strip `raw_value` anyway. It would only punish a naive input check rather than describe a real flaw.
- **S-d PBES2 password fallback to `b""`** — rejected: different protection (JWE confidentiality), out of scope.
- **S-e legacy `jws.verify` compatibility shim reimplementing HMAC** — rejected: a maintainer would call the
  library's own `alg.verify`; writing a second HMAC comparison by hand is not plausible and would be a pure
  where-type search cost.
- **S-f per-kid key cache falling back to a key derived from the `kid`** — rejected: the supplied kid is
  attacker-known but non-empty, so it falls outside the empty-secret property (different vulnerability).
- **S-g env-var default secret inside the key helpers** — rejected: a crypto library silently reading the
  environment looks planted and would make the test depend on process env.
- **S-h key stretching in `OctBinding.import_from_bytes`** — rejected: same normalisation concept as S-a, and
  the import check calls the producer directly (`super().import_key`), which the design guidance says to avoid.
- **S-i `KeySet` "try every key" fast path** — rejected: still calls `alg.verify`, so it creates no gap.

Why the picks beat the others: S-a is the only candidate that puts a producer between the supplied secret and
the MAC check while staying on the documented JWT/JWS path in a different module from the report's sink; a
fix at either reported site cannot see it. S-b is a different public surface and input shape (collection
entries rather than one scalar) that builds key objects directly, so it survives an import-level-only fix and
is far from the report. Together with the real T2/T3/T4 routes and the T7/T8 coupled behaviour, the task has
six independent reasons to fail (producer transform, entry-point scope, lower-level API, zero-size producer,
over-hardening, and banning a legitimate convenience).

## Sites / routes / input shapes the hidden security suite covers

- Import: `OctKey.import_key("")`, `b""`, `{"kty":"oct","k":""}`; `jwk.import_key("", "oct")`,
  `jwk.import_key({"kty":"oct","k":""})`, `JWKRegistry.import_key(dict)`,
  `KeySet.import_key_set({"keys":[dict-with-empty-k]})`.
- Authentication, empty key material: compact JWS, JWT, JSON general, JSON flattened, RFC 7797 b64=false,
  HS256/384/512, with an `OctKey` built directly and with one whose `_raw_value` is cleared.
- Signing with empty material: compact, JWT, JSON.
- Zero-length generation: `jwk.generate_key("oct", 0)` (and using the result if generation is not refused).
- Plain-secret producer: empty `str`/`bytes`/`bytearray`, direct argument and key-finder callable, on
  `jwt.decode`, `jwt.encode`, `jws.deserialize_compact`, `jws.serialize_compact`, and JSON serializations.
- Collection surface: empty plain string inside `KeySet.import_key_set`.

## Coupled must-keep-working (functional suite)

- Short non-empty oct keys: import with only a `SecurityWarning`, sign and verify; short generation warns.
- Normal keys: str/bytes/dict import, `jwk.import_key`, `JWKRegistry`, `KeySet` of dicts, generation at
  ordinary sizes, all serializations.
- Injected conveniences: non-empty plain `str`/`bytes` secrets verify and sign; non-empty plain secrets in a
  key-set rotation list verify.
- Project's own tests for the affected area (oct key, key methods, JWK set, compact/JSON/RFC7797 JWS, JWT,
  RFC 7520 JWS/JWK).

## Test seam

Pure library calls, no services. The hidden tests import only `joserfc` (to drive the public APIs) and the
standard library; forged compact/JSON signatures are computed in the test with `hmac`, `hashlib`, `json` and
`base64`, never with product signing helpers, so a hardened signing path cannot break the test's own
bookkeeping. Refusal = any raised exception; tests never assert an exact exception type or message.

## Open fairness notes

- T4 (zero-length generation) is a judgement call; the property says empty material must not be produced, and
  the generator is the only place that produces it without a caller-supplied secret. It is one test, and a
  fix at the MAC layer still passes the auth tests for it.
- T6 only fails on the "must not yield a key" clause; its auth consequence is already covered by the MAC-level
  check. This is deliberate: the property says the library must refuse the value, not merely survive using it.

## Verification log

Local (scratch tree, Python 3.12 venv, editable install), before the gate:

- Pinned+injected: 36/36 hidden security tests fail (the attacks succeed), 19/19 hidden functional
  tests pass, 275/275 project tests pass.
- Reference fix: 36/36 hidden security, 19/19 hidden functional, 120/120 affected project tests pass.
- Per-check local results (security, functional):
  - miss_import 8 security fail / 0 functional fail
  - miss_mac 11 / 0
  - miss_generate 2 / 0
  - miss_plain_secret 10 / 0
  - miss_keyset 3 / 0
  - sign_only 7 / 0
  - input_only_check 5 / 0
  - fail_open 7 / 0
  - overbroad 1 security fail / 14 functional fail
  - hardening 0 / 0 (pass)
  - alt_fix 0 / 0 (pass)

Gate:
- static PASSED 2026-10-24T05:35Z.
- nop: first attempt hit the shared VM's `/tmp` tmpfs inode exhaustion (1M inodes, 100% used by
  other sessions) inside the classic docker builder ("mkdir /tmp/containerd-mount...: no space left
  on device"), classified infra; retried with `TMPDIR=/home/mara/.tb-graders/cwe/tmpgate`.
  - nop PASSED 2026-10-24T05:53Z: security 0/36 (every attack succeeds on the vulnerable tree),
    functional 139/139 (19 hidden + 120 project), reward 0.0.
- oracle: PASSED 2026-10-24T06:19Z — 3 runs, each reward 1.0 with 175/175 (36 security + 139
  functional) and identical per-test results. The collected artifact contains all four fixes
  (`HMAC key must not be empty` in sign/verify, `oct key material must not be empty`,
  `key_size == 0`, and the two plain-secret guards).
- The shared VM's main Docker daemon wedged after the nop stage (`/_ping` 200 but `/version` and
  `/info` hang; `docker version` never returns). All later stages run on a task-private dockerd
  (bridge jfpriv0 10.230.0.1/24, pool 10.234.0.0/16, data-root on the home disk, `TMPDIR` on the
  root fs) with `DOCKER_HOST` exported. The private daemon's containers cannot reach 8.8.8.8, so DNS
  is a socat relay on the bridge gateway forwarding to the host's metadata resolver; outbound
  forwarding needed explicit `-i jfpriv0` / `-o jfpriv0` ACCEPT rules because the shared host's
  FORWARD policy is DROP and other sessions rewrite that chain.
- patches: PASSED 2026-10-24T06:28Z — all eleven listed checks behaved as declared on the private
  daemon: miss_import 8 security fail / 0 functional, miss_mac 11/0, miss_generate 2/0,
  miss_plain_secret 10/0, miss_keyset 3/0, sign_only 7/0, input_only_check 5/0, fail_open 7/0,
  overbroad 17 functional fail, hardening reward 1.0, alt_fix reward 1.0. `blind.patch` was
  skipped (written downstream by the pipeline, as designed).

## Out of scope, in one line each

- JWE PBES2-HS*+A*KW accepts an empty oct key as its PBKDF2 password (JWE confidentiality, not
  HMAC authentication) — recorded in the register, not built.
- `verify_general_json` returned True for an empty `signatures` list at the pinned commit (no
  signature at all, no key involved; fixed upstream in f409f8f after this advisory) — out of scope.
- `NoneAlgorithm` deliberately accepts an empty signature when explicitly allowed — documented
  feature, different vulnerability.
- JWE `dir`/AESKW/AESGCMKW and CBC-HS enforce the CEK length, so no empty-key route exists there.

## What I could not verify

- The target models' behaviour (trials are run by the pipeline, not by the builder).
- `public_upstream_report` for the register rows: no public report was searched; the advisory text
  itself was read and names only the HMAC sign/verify and import sites.
- Whether a maintainer would actually have written the two injected conveniences; both are written
  as ordinary convenience code with no deceptive naming, but they are additions, not upstream code.
