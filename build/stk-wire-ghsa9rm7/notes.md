# stk-wire-ghsa9rm7 — build notes (abandoned)

Start: 2026-10-26T12:28:58Z. End: 2026-10-26T12:55Z (UTC).

Outcome: **abandoned before writing a task tree**. The reader's stack is exactly the union of
the two published fixes, so the rule-12 recall check would pass; the remaining hard candidates
are out of this advisory's protection. No task tree, tests, checks or control were written.

## The record's traps and what verification found

Pinned = 50ba803e865fcf43d4a4718dce851e6cf6d981dc (`git rev-parse e4e56fa^` == pinned; verified).

- T1 (32-bit positive length overflow, `ByteArrayProtoReader32.kt:131-137`, evidence also
  `:388,416,433,441,448`, `IntArrayList.kt:56,61`, `KotlinGenerator.kt:2189,2194`):
  **fixed by B** (25ebcabb "Prevent overflow for 32-bit length integers", release backport
  082d5d83). B replaces `limit = pos + length` with `checkedLimit(length)` and routes every
  read/skip/limit computation through `remainingInLimit()`/`checkedLimit()`.
- T2 (negative length in the 32-bit `skipGroup`, `ByteArrayProtoReader32.kt:229-232`):
  **fixed by A** (e4e56fab "Add negative-length check in skipGroup", release backport 47d5b0db).
  A adds `if (length < 0) throw ProtocolException(...)` in that branch.
- T3 (negative length in the 64-bit `ProtoReader.skipGroup`, `ProtoReader.kt:268-272`):
  **fixed by A** (same commit, second file).

Evidence: `git log 50ba803e..25ebcabb -- wire-runtime/src/commonMain wire-runtime/src/jvmMain`
returns exactly two commits, e4e56fab and 25ebcabb. No other commit touches the runtime in the
fix range. A+B's own regression tests are the exact payloads for all three traps
(`9b060a80ffffff0f9c06`; `0affffff07`, `1affffff07`, `0b0affffffff070c`; and the
fixed32-past-the-message-limit case, both readers).

## Why the stack cannot be built

1. **Rule 12 (recall).** `upstream_fix.patch` = A+B; it closes T1, T2 and T3, so the recall check
   would pass. The task would add nothing beyond what upstream shipped.
2. **Rule 1/2 (independent hard concepts).** The reference fix has two independent edit sites,
   not three: the 32-bit reader (checked limit + negative-length skipGroup) and the 64-bit reader
   (same two). T1 and T2 are closed by one helper design in one file. Also T1 is tier
   easy/medium in the record, so as a singleton it fails rule 2; grouping T1+T2 leaves only two
   hard concepts (T3 is the third trap but the second site).
3. **No in-scope uncovered route.** The only routes not closed by A+B are outside this
   advisory's protection: the Swift negative-length `skipGroup` (GHSA-9rm7 explicitly tracks it
   under the separate GHSA-86wm-r4c5-2rc9 / CVE-2026-61695, and upstream fixed it in
   24043b6b3), and an unchecked-exception path in `MapProtoAdapter.decode`
   (`ProtoAdapter.kt:745-755,766-776`: an unknown tag in a map entry is "ignored" without
   consuming its value, so the next `nextTag()` throws `IllegalStateException`; a message-valued
   entry with the value omitted hits `check(value != null)`). Neither is a length-delimited-size
   defect, and the map path is still present on upstream master (82f49bf4e), so it is not an
   already-fixed advisory route. Noted, not built on.
4. **No injections.** The reader's plan does not ask for injected siblings; the build prompt
   allows them only where the plan asks, and they would not be "code the code supports".

## Verification performed

- Read the pinned readers, both published fix diffs, the upstream regression tests, and the
  full commit range (above).
- Built `wire-runtime` on the pinned tree with A+B applied (Gradle 9.5.0, JDK 21;
  `:wire-runtime:jvmTest` green, 5m21s).
- Differential probe (`AnyMessage.ADAPTER.decode(ByteArray/ByteString/BufferedSource)`, manual
  `ProtoReader32`/`ProtoReader` tag loops, the public `ProtoReader32(source,pos,limit)` slice,
  and a map adapter) over the three upstream payloads, 21 structured tag/length cases, and 15k
  random payloads biased to length/group bytes. Post-A+B: no non-IOException failure on any
  length route; the only findings were the map-adapter `IllegalStateException` above, on both
  readers. (Pinned tree: the known traps reproduce by construction; the same probe was not run
  to completion because the shared host was heavily loaded, and it is not needed for the
  decision.)

## Could not verify

- The release-branch commits (47d5b0db, 082d5d83) were not applied literally; the master-lineage
  equivalents (e4e56fab, 25ebcabb) were used, which `git show --stat` shows are the same changes.
- Swift was not built or run (out of the Maven artifact for this task; its negative-length route
  is a separate advisory).
- The reference-fix effort for T4 (caller-supplied `pos`/`limit` in the public factory) was not
  probed; the record dismisses it as caller data, and B's `init` bounds already prevent it
  (though with `IllegalArgumentException`).

## Outside scope (one line each; not built on)

- Swift negative-length `skipGroup` (GHSA-86wm-r4c5-2rc9 / CVE-2026-61695).
- Map-entry unknown-tag / omitted-message-value `IllegalStateException` in `ProtoAdapter.kt`
  (never fixed upstream; not a length protection).

## Scratch

Work tree and probes: `~/.tb-graders/cwe/work/stk-wire-ghsa9rm7/` (`w` pinned clone, `wfix`
A+B, `wpin` pinned+probe, `gcache` Gradle cache; `ProbeTest.kt` is builder-only and was never
placed in the source repository or a task image).
