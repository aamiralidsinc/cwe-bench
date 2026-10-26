# stk-jwcrypto-ghsafjrm build notes

Start: 2026-10-26T12:30:53Z (from start_utc.txt). End: PENDING (fill after the gate).

Pinned: latchset/jwcrypto 240cc60fe4fe7458d3a7828c3e793795eb59a438, the direct parent of A
90477a3b6e73 (verified with git rev-list --parents). B 25db861d8b29 is the later fix and A is its
ancestor. The advisories are GHSA-j857-7rvv-vj97 / CVE-2024-28102 (A) and GHSA-fjrm-76x2-c4q4 /
CVE-2026-39373 (B); both are about compressing a JWE payload with "zip":"DEF".

## Levers (one line each)

- T1 (mimo, advisory route): a small compressed payload inflates without bound at
  `jwcrypto/jwe.py:422-429`; a length check after inflating still allocates the expansion, and
  decrypt()'s broad catch at `jwcrypto/jwe.py:450-466` then returns it. Reason to dismiss: the tag
  verifies first, so only a key holder triggers it, and a post-hoc length check looks sufficient.
- T2 (deepseek, uncovered upstream): `jwcrypto/jwe.py:450-457` decrypts once for every recipient
  entry and never stops after a success, so a per-attempt bound leaves the total work multiplied.
  Reason to dismiss: trying every recipient is normal recipient selection and each attempt is now
  bounded.
- T3 (deepseek, uncovered upstream): `jwcrypto/jwe.py:19, 160-178, 373` merges the compression
  declaration from the shared unprotected and per-recipient headers, so unauthenticated data
  decides whether to inflate; JWE never enforces must-protect (JWS does at jws.py:246). Reason to
  dismiss: the sink reads the merged header, so a sink-level bound covers every source, and
  requiring protection would refuse tokens that work today.

## What was verified (no Docker)

- All three routes on the pinned tree: 16 MiB attack from a ~16 KiB payload; 8 recipients produce
  8 decompressions (16 MiB in one call); zip in the shared unprotected header and in a
  per-recipient header each inflate 2 MiB despite a protected header with no zip.
- The natural post-hoc guard is masked: decrypt() swallows its exception and returns the 16 MiB
  because self.plaintext is truthy.
- Project tests: `python3 -m pytest jwcrypto/tests.py` -> 103 passed on the pin (Python 3.13,
  cryptography 43.0.0).
- Hidden suites on every tree: pin 0/6 security + 6/6 functional; reference 6/6 + 6/6;
  miss_output_bound 3/6; miss_recipient_loop 5/6; miss_zip_protection 4/6; masked_check 3/6;
  input_cap_only 0/6; upstream_first_fix 0/6; upstream_fix 0/6; hardening 6/6; alternative 6/6;
  refuse_all 6/6 security + 4/6 functional; adjacent_api 6/6 security + 5/6 functional.
- Control task: same runs with its 4 C1-only security tests: pin 0/4 + 6/6; c1_only 4/4 + 6/6;
  input_cap_only 0/4; masked_check 0/4; hardening 4/4; alternative 4/4; refuse_all 4/4 + 4/6;
  adjacent_api 4/4 + 5/6.
- Current upstream (read-only, origin/main 053108a): T2 is closed there by a 10-recipient cap plus
  stop-after-first (later than the advisory fixes); T3 is still present (the merge and the
  must-protect=False registry entry are unchanged).

## Environment note

The first container build failed at `pip install --no-deps -e .` followed by an import: jwcrypto
declares `typing_extensions >= 4.5.0` in setup.py but `--no-deps` skipped it, and `jwk.py` imports
`deprecated` from it. Both Dockerfiles now install `typing_extensions==4.16.0` explicitly; the
environment image builds and `import jwcrypto.jwe, jwcrypto.jwt` succeeds.

## What was not verified / could not verify

- No model trials were run (not permitted during the build), so the bar (both target models failing
  all three attempts) is not measured here.
- The reader's record rates the repeated-recipient route (its T3) easy/easy and says a per-recipient
  guard covers it; the screener's design rates that route deepseek-hard and treats it as a separate
  edit site. I verified the route is real and independent of the sink bound (the miss patch fails
  only it), but its difficulty for the models is from the screener, not re-measured.
- The report states an 8 MiB allowance. Upstream B chose 100 MB; the oracle uses the report's
  allowance so the tests stay small and the contract is explicit. The published A+B patch therefore
  also fails the task's own T1 test (it accepts a 16 MiB expansion); that is expected for a recall
  check and is noted in the manifest.
- The listing check was not run (post-build step). The report states one resource-bound property
  with "in total" and one integrity property, and names no route; T1 is the advisory route and the
  two hidden traps are covered by those general properties only.

## Scope note

T3 is an integrity-of-the-declaration property, not the CWE-409 resource bound itself; it is built
because the advisory's decompression decision is driven by unauthenticated data. T2 is resource
amplification across a single call. Nothing else in the tree (e.g. the separate PBES2 iteration
budget) was built on.
