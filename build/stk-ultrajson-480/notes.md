# stk-ultrajson-480 — build notes

- start: 2026-10-26T02:20:32Z
- end: (set at the end of the build)

## Levers (one line each)

- T1, advisory route, pattern A: bytes values whose 2/3/4-byte sequence has a byte in a continuation
  position that is not `0b10xxxxxx` are folded into a different code point instead of refused
  (`src/ujson/lib/ultrajsonenc.c:350-368,382-404,417-432`; value branch `objToJSON.c:426-438`).
- T3, pattern A, published-fix far site: each encoder arm's end-of-buffer guard is one byte short
  (`end - io < 1/2/3`), so a sequence cut at the end is completed with the NUL terminator
  (`ultrajsonenc.c:355,388,421`).
- T11, pattern B, uncovered route: a bytes object key goes through `Dict_convertKey` and reaches the
  shared encoder without the bytes-value branch, so a value-side guard leaves keys open
  (`objToJSON.c:214-242`, `ultrajsonenc.c:690-703`).
- T2, pattern A, published-fix far site: the 4-byte arm has only the overlong test, so a complete
  sequence above U+10FFFF (lead `f4` with second byte >= `90`, or `f5`-`f7`) is escaped into
  surrogate halves (`ultrajsonenc.c:428-441,518-537`).
- T4, pattern B, uncovered route: the decoder's continuation test is `(oct & 0x80) != 0x80`, which
  accepts a start byte in a continuation position in all three arms
  (`ultrajsondec.c:527-535,544-555,567-578`).
- T5, pattern B, uncovered route: `g_decoderLookup` maps `0x80`-`0xBF` to length 1, so a lone
  continuation byte where a start byte is required becomes U+0080-U+00BF
  (`ultrajsondec.c:342-355,519-523`).
- T10, coupled must-keep value (MiMo-type): the project's existing surrogate-escape representation
  (`tests/test_ujson.py:643-654,684-686`) must keep working for values, keys, parsed bytes and
  `ensure_ascii=False`; a strict RFC-3629 validator breaks it.

## Verified

- Every security case is absent on the pinned tree and refused by the reference:
  37/37 security tests pass with the reference, 0/37 on the pinned tree; 411/411 functional tests
  pass on both. Built locally with CPython 3.12 and the vendored double-conversion sources.
- The project's own pinned `tests/test_ujson.py` (380 collected cases) passes on the pinned tree and
  on the reference; the one free-threading test skips on CPython 3.12 and is filtered by name in
  `tests/test.sh` because score.py counts a skip as not-passed. The test module and its fixture
  files are copied unmodified; the project's runner-only `conftest.py` is not copied because on
  pytest 8.4 its `--leak-max-loops` option is registered after option parsing, which makes its own
  collection hook crash (`AttributeError`) and would score the functional group as failed.
- Per-concept miss patches leave only that concept's security tests failing with every functional
  test passing: G1{T1,T3,T11} 21 failures, G2{T2} 8, G3{T4} 4, G4{T5} 4.
- Recall: the published fix alone (169eaf) leaves exactly the 8 decoder security tests failing.
- `decoder_only` leaves 29 encoder tests failing; `value_only` leaves 13 key tests failing;
  `functional_overbroad` breaks 23 functional tests; `refuse_all` breaks 21; the alternative
  boundary-validation design and the hardening design both score 1.0.
- Every `checks/*.patch` applies with `patch -p1` to a pristine checkout of the pinned commit.
- `check_stack.py` conforming (4 concepts, pattern H4); static gate passes for both the stacked task
  and the control.
- Control: reference and both check patches behave as declared (16 security, 411 functional).

## Could not verify

- The full advisory text was not available. That the advisory covers only dumping is judged from the
  screener record, the published fix's landing point and its decoder changes being error wording
  only; the reading property is the task's own extension (the reader's T4/T5 routes).
- The decoder routes were fixed upstream later, in `d801f77` (2026-06-27), a separate commit with no
  advisory of its own. It is a descendant of the pinned commit and is deliberately not part of
  `checks/upstream_fix.patch`; the register records `present_in_latest = no`.
- The listing check (`pipelines/stacking/4-listing/run_listing_check.sh`) was not run: it needs a
  model, and the build prompt forbids running target models. The report states each protection once
  over its protected data and never names a hidden route.
- No ASAN/valgrind run. The encoder's one-byte over-read at the end of a buffer is confined to the
  terminator for the Python bindings; it was observed deterministically on this allocator but not
  measured under a sanitizer.
- The alternative design's refcounting was exercised by the project suite (including its refcount
  checks) but not audited by hand.

## Fairness notes

- The project's own tests are visible in `/workspace/tests`; they require the surrogate values and
  the `OverflowError` type, so both coupled values are discoverable without the report naming them.
  A boundary-level fix that raises `UnicodeDecodeError` fails the visible suite, which is the
  intended coupled behaviour.
- All security inputs are literal byte strings; expected outcomes are "raises", never one exact
  exception type or message, so any clean refusal passes.

## Out of scope (not built on)

- The decoder reads a byte past the end of a buffer that is not NUL-terminated (`array.array`,
  `memoryview`): a separate bounds family, not the UTF-8 property; left untouched.
- The `__json__` raw-bytes producer and the `forceASCII=0` passthrough are already closed end to end
  by the `PyUnicode_DecodeUTF8(..., "surrogatepass")` backstop and were not graded.
- The `reject_bytes` policy gap for bytes keys (T9 in the reader record) is a bytes-policy choice,
  not the advisory's UTF-8 property; not graded.
