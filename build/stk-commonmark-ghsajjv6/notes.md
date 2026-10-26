# stk-commonmark-ghsajjv6 build notes

Started 2026-10-26T02:27:36Z. Finished 2026-10-26T__END__Z.

## What the task is

thephpleague/commonmark pinned at 6cfa16c7f37e2748114c56d9375a09af656b995c, the parent of
advisory A's first fix (2d4c0fafa625). The report shows one quadratic conversion path (unpaired
smart quotes) and states a general invariant: conversion time stays proportional to input length.
The reference fix is the three published fixes (2d4c0fafa625, 04a5d11ef6bf, 2f611b599c51) plus a
generalisation for non-class attribute names, which those fixes leave quadratic.

## Levers (one line each)

- T1, advisory route, type both: unpaired smart quotes re-copy the growing text node in the shared
  adjacent-text merge — src/Node/Inline/AdjacentTextMerger.php:92-103.
- T3, published-fix far site, type mimo: a multi-line attribute block re-merges the whole
  accumulated set per continuation line — AttributesBlockContinueParser.php:58-60 with
  AttributesHelper.php:123-137.
- T4, published-fix far site, type both: attribute nodes targeting one element re-merge and
  re-filter the whole accumulated set per node, for classes and for every other name —
  AttributesListener.php:61-66,151-153.
- T5, published-fix far site, type deepseek: target resolution re-scans the sibling chain per
  node (inline runs at the start of a block and contiguous TARGET_NEXT block runs) —
  AttributesListener.php:83,96,107,145.

Uncovered route used for the recall check: T3 and T4 also cover non-class attribute names. The
published fixes for the stacked advisories (2.9.1) only special-case `class`; the same quadratic
remains for distinct attribute names. A later advisory (GHSA-8rr7-cvq3-gmfh, 2.10.0) fixed the
same accumulation, so `present_in_latest` is recorded as no in the uncovered-routes register.

## Verified

- Every security test fails on the pinned code (all 8 time out or exceed the in-test bound) and
  passes on the reference fix. Reference-fix security group: 8/8 pass in ~8 s; pinned: 8/8 fail.
- Measured pinned vs reference on the build VM (pinned / reference): quotes 83 s / 1.4 s;
  inline attribute run at start 138 s (extrapolated from 15.3 s at 12k) / 0.9 s; block attribute
  run 108 s (from 12.0 s at 8k) / ~2 s; inline class run 114 s (from 18.3 s at 24k) / 0.5 s;
  inline named attribute run 126 s (from 14.0 s at 16k) / 0.6 s; block class lines 114 s (from
  18.3 s at 24k) / 0.5 s; block named attribute lines ~81 s (5.8 s at 32k) / 0.8 s.
  Security tests bound a conversion at 20 s and the runner kills at 35 s.
- Rendered output is byte-identical to the pinned implementation across the project's Attributes
  and SmartPunct fixtures, including attribute order and duplicate classes, and across every
  fixture in the functional group.
- Project tests: the Attributes and SmartPunct suites pass on the pinned commit and on the
  reference fix (110 tests, 180 assertions). The full unit+functional suite passes (4250 tests)
  except two Embed tests whose optional package is not in the reduced verifier vendor.
- Every check patch was applied to a clean pinned checkout and run locally: miss_T1/T3/T4/T5 each
  fail only their own concept's security tests with the functional group green; upstream_fix and
  upstream_first_fix fail security with functional green; reported_route_only and
  inline_direction_only fail security; drop_attributes, crash_large and class_as_array fail the
  functional group; hardening and alt_fix score 1.0 (alt_fix fixes T1 at the listener layer by
  merging each container once, leaving the shared merger untouched).
- Static checks: common/gate static, common/builder/conformance_check.py and
  pipelines/stacking/3-build-gate/check_stack.py all pass for both the task and its control.

## Could not verify / open questions

- The reader record path named in the manifest (pipelines/stacking/out/reader/
  h3-ghsa-jjv6-8j6v-6j52.json) does not exist in this checkout; the record used here is the one
  supplied verbatim in the build prompt. All five traps except T2 were re-verified against the
  pinned source; T2 was dropped by the reader because it shares T1's fix site.
- Timing margins were measured on a loaded shared VM with the host's full CPU pool, not inside the
  gate's 2-CPU verifier; the sizes leave a 4x-8x margin over the 20 s bound on the pinned code and
  a 10x-60x margin under it for the reference. The nop/oracle gate stages are the real check.
- The environment image build and the project's own suite inside that image are exercised by the
  gate, not by this session.

## Scope note

One route in the reference fix (non-class attribute accumulation) is covered by a later upstream
advisory (GHSA-8rr7-cvq3-gmfh) than the two listed for this task; it is the same protected sink,
in the same repository, at the pinned commit, and the published fixes for the listed advisories
leave it open. It is recorded in build/audit/uncovered-routes.tsv. Nothing else outside the
listed advisories' protection was used.
