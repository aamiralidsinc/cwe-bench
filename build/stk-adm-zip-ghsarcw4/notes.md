# stk-adm-zip-ghsarcw4 — build notes

- Started: 2026-10-26T12:29Z
- Ended: (filled after the gate run)

## Task

adm-zip (JavaScript, npm), pinned at `8592b1574e7e6e72d06e1afee5d7f0588d541950` (v0.5.18), the direct
parent of the first published fix `2450dcf417aa`. Pattern A+B, stacked H3b2. The second published
fix is `491600683dac`. The report leads to the second advisory's route (a declared uncompressed size
of zero disables the output cap).

## Levers (one line each)

- T1 — second implementation (uncovered upstream), DeepSeek-type — `methods/inflater.js:12-22`
  (reached from `zipEntry.js:124-131`). The streaming inflater is handed the same cap option object
  as the synchronous one, but the streaming API ignores it and the helper accumulates every emitted
  chunk without ever counting the total. Reason to dismiss: the shared option object makes the
  asynchronous path look covered by the synchronous guard.
- T2 — the report's route (advisory), MiMo-type — `methods/inflater.js:5`. The cap option is built
  only when the declared size is greater than zero, so a declared size of exactly zero passes no
  budget. Reason to dismiss: zero is the normal encoding of an empty entry, so `> 0` reads as a
  deliberate empty-file carve-out; rejecting zero breaks genuinely empty DEFLATED entries.
- T3 — trusted declared size (published fix's own site), both-types — `zipEntry.js:103,117`. The
  same attacker-controlled uncompressed-size field sizes the output buffer before any data is read
  and also sets the decompression budget. Reason to dismiss: large and ZIP64 entries are legitimate,
  so the declared size looks like the right value to allocate and to cap at.

Stacking concepts: `["T1"]`, `["T2"]`, `["T3"]` — three independent fix sites. The reader's T4
(ZIP64 zero-budget) and T5 (pre-Node-15 option branch) were verified but not built as levers; see
"What could not be verified / what was dropped".

## What was verified

- Every route was reproduced on the pinned tree before building (probe scripts under
  `~/.tb-graders/cwe/work/stk-adm-zip-ghsarcw4/probes/`):
  - T2 synchronous: declared 0, 64 MiB stream -> 0-byte result, no error, ~128 MiB live
    ArrayBuffer growth.
  - T1 asynchronous: declared 1 KiB, 64 MiB stream -> 64 MiB returned, ~128 MiB growth; declared 0
    behaves the same.
  - T3 stored and deflated: declared 1 GiB, ~1 MiB of data -> ~1 GiB allocated before the CRC check.
- Local scoring with the real `tests/score.py` over the hidden suites and the project's own mocha
  suite:
  - pinned: security 0/6, functional 31/31 (reward 0.0);
  - reference (A's allocation fix + B's unconditional cap + the async error channel B relies on):
    security 6/6, functional 31/31 (reward 1.0);
  - miss_T1: 4/6, functional 31/31; miss_T2: 4/6, functional 31/31; miss_T3: 4/6, functional 31/31;
  - upstream_first_fix (A alone): 2/6; upstream_fix (A + B's size-0 cap): 4/6;
  - ff_refuse_all: functional 25/31; ff_crash_as_refusal: 4/6; ff_check_after_adjustment: 2/6;
  - pass_hardening and pass_alt: reward 1.0.
  - control: pinned security 0/2, functional 31/31; floor-1 reference 2/2 + 31/31 (reward 1.0).
- The project's own suite at the pin: 93 tests pass in the verifier with `test/zip64.test.js`
  excluded. That file builds 65,536 entries as a performance case; at the pin it spends ~10 s and
  trips its own `this.timeout(10000)` under load, and it is unrelated to the affected decompression
  area.
- The pinned tree does not contain the advisories' regression tests (`test/decompress_bomb.test.js`
  is added by the first fix commit, not present at the pin).

## Recall-patch attribution (deliberate)

`checks/upstream_fix.patch` is A's allocation fix plus B's size-0 cap (the two stacked advisories'
published source changes). B's commit `491600683dac` additionally contains an asynchronous-cap fix
for a **different** advisory (GHSA-c6fg-446q-cg94 / GHSA-v429-h5qx-84wm, per the commit's own
comments); that change is excluded from the recall patch because it fixes neither stacked advisory.
Consequence, stated plainly: if the whole B commit were applied, T1 would also close, and the recall
check would pass. With the stacked advisories' own fixes, the two asynchronous cases still fail.
`checks/upstream_first_fix.patch` is A alone; it fails four security cases.

## What could not be verified / what was dropped

- T4 (ZIP64 route: a 64-bit size of 2^32 wraps to 0 in the uint32 setter) is reachable at the pin,
  but a fix that faithfully honours 64-bit sizes makes the shape harmless (the output stays within
  the declared size), so a security test for it would reject a valid fix. It is covered by T2's
  one-byte-floor fix instead and is not built as its own lever.
- T5 (the `version >= 15` branch: on Node 12/14 no `maxOutputLength` exists and the synchronous
  path is uncapped) is real, but the graded runtime is Node 20 and a synchronous in-JS fallback for
  old Node is not a ~45-minute fix; requiring it would be unfair. Not built.
- The advisories' "honest bomb" shape (a large declared size that matches the real output) cannot
  be distinguished from a legitimate highly compressible file without a ratio limit, which the
  fairness analysis rejects. The property is therefore about the declared-size budget and the
  allocation, not about absolute output size.
- Whether Buffer.alloc near 2^32-1 throws on every Node/arch was not executed; the tests use 1 GiB,
  which allocates on every graded Node and keeps the child well inside the verifier's 4 GB.

## Machine notes

- Verifier-specific measurement detail: live ArrayBuffer growth (`process.memoryUsage().arrayBuffers`)
  separates an allocation from a refusal; RSS stays small because untouched zero pages are not
  resident, so RSS alone would miss the preallocation route.
- The hidden security cases each run in a fresh `node` child so an OOM or an uncaught throw is an
  isolated test failure, not a verifier crash.
