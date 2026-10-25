# yara-x-ds — build notes (build-v1, pattern A+B, injected)

Advisory: GHSA-2JX3-FF3V-J7JJ (virustotal/yara-x, CWE-502 unvalidated deserialization →
out-of-bounds read / invalid UTF-8 UB). Pinned 4fbaf55606e06af6e109d02b764a9190edf8c4ed,
fix 25efa375572efcfbe880a263ee3b0932d4b61a24.

Start (UTC): 2026-10-24T02:24:46Z
End (UTC): TBD

## One-line summary

`Rules::deserialize` (and `deserialize_from`) decodes caller bytes with bincode and trusts every
field: out-of-range table indexes are later used with `get_unchecked` in the scanner / regex VMs,
non-UTF-8 literal bytes are later turned into `&str` with `to_str_unchecked`, and the published
fix only re-checks the atom→sub-pattern ids (with an off-by-one that still accepts `id == len`).

## Security property (stated once; instruction uses this wording, no locations)

A compiled-rules blob is internally consistent when (a) every identifier or offset it carries that
the engine later uses to address one of its internal structures is within that structure, and (b)
every value it designates as text is valid UTF-8. The operation that converts caller-supplied bytes
into usable rules must reject an inconsistent blob with an error, and must never return rules that
can later read out of bounds, hand back invalid text, or crash. The same rule applies however the
bytes reach the converter.

## Levers

L1  SHAPE TRAP (how) — atom→sub-pattern id exactly equal to the table length.
    shape: `SubPatternAtom.sub_pattern_id == sub_patterns.len()`; the natural `< len` repair
    (the published fix's shape) accepts it, and `get_unchecked(id)` reads one past the end.
    where: lib/src/compiler/rules.rs:418 sink, used at lib/src/scanner/context.rs:861.
    reason to dismiss / why models skip: the report leads to the atom check; `< len` reads as the
    complete bound and the equality corner looks covered.
    coupled legit: a plain rule must still round-trip and scan; a rule with no atoms (empty atom
    vector) must be accepted (a naive `0 >= 0` check rejects it).

L2  ROUTE WHERE PROTECTION NEVER EXISTED (how) — anchored sub-pattern ids.
    shape: `anchored_sub_patterns` entry out of range; every scan consumes the vector before the
    Aho-Corasick phase, so any scan reaches `get_sub_pattern` with it.
    where: lib/src/scanner/context.rs:1147-1151 (unmodified upstream; published fix ignores it).
    reason to dismiss: anchored patterns are a separate optimisation path that does not use the
    atoms the fix reasons about.
    coupled legit: a literal anchored at a fixed offset (`at 0`) must round-trip and match.
    Confirmed behavioural: pinned accepts; scanning with an out-of-range id segfaults.

L3  ROUTE WHERE PROTECTION NEVER EXISTED (how) — regexp code locations.
    shape: `SubPatternAtom.fwd_code` / `bck_code` pointing beyond `re_code`.
    where: lib/src/re/thompson/pikevm.rs:199 / :400 and lib/src/re/instr.rs:429-431, reached from
    lib/src/scanner/context.rs:1383-1450 when the atom matches a regexp sub-pattern.
    reason to dismiss: bytecode validity reads as a compiler invariant inside a separate engine
    module tree.
    coupled legit: a regexp pattern must round-trip and match after the fix.
    Confirmed behavioural: pinned accepts; scanning a matching byte with an out-of-range code
    location reads outside `re_code`.

L4  PRODUCER OFF THE CHECK'S PATH (how) — metadata text vs. the literal pool.
    shape: `MetaValue::String(id)` whose lit_pool bytes are not valid UTF-8. The UTF-8 invariant is
    established by the compiler when it interns a meta string; `deserialize` never calls the
    compiler, and the accessor's comment assumes the invariant.
    where: lib/src/models.rs:204-213 (published far site); invariant produced by
    lib/src/compiler/mod.rs (literal interning), never re-established on load.
    reason to dismiss: a read-only model accessor in another module; "the type says String, so the
    pool content must be UTF-8".
    coupled legit: `MetaValue::Bytes` legitimately holds arbitrary (non-UTF-8) bytes and binary
    patterns hold arbitrary literal bytes — an over-broad "pool must be UTF-8" check breaks both.
    Confirmed behavioural: pinned accepts; `Rule::metadata()` returns a `&str` over invalid bytes.

L5  INJECTED SIBLING — fast-scan bitmap.
    shape: a pattern id carried by the blob that is beyond `fast_scan_patterns` while still inside
    the bitmap sized by `num_patterns`; the scanner's fast-scan path addresses the bit vector with
    the blob's pattern id.
    where: lib/src/compiler/rules.rs:603-604 (`is_fast_scan`, injected `get_unchecked`), consumed at
    lib/src/scanner/context.rs:1777.
    reason to dismiss: the bit vector is treated as compiler-derived bookkeeping, not blob data;
    `num_patterns` looks like the only bound that matters.
    coupled legit: a legitimate compiled rule set scanned with fast-scan mode enabled must still
    find matches.

L6  INJECTED SIBLING — literal-pool id in the hot verification path.
    shape: `SubPattern::Literal { pattern }` / `Base64` / `Xor` literal id out of the pool range;
    the scanner resolves it on every atom match.
    where: `BStringPool::get_bytes` call sites in lib/src/scanner/context.rs:891-1043 (injected
    `unwrap_unchecked` in the hot path).
    reason to dismiss: pool ids are compiler-produced and the pool is infrastructure, so a
    maintainer treats a missing id as impossible.
    coupled legit: text patterns, hex patterns with arbitrary bytes and bytes metadata must keep
    resolving from the pool.

## Candidate list (all found; picks in bold)

Real, unmodified upstream at the pinned commit:
1. atoms[].sub_pattern_id → scanner (published fix covers, off-by-one corner) — **L1**.
2. anchored_sub_patterns[] → scanner (published fix never touches) — **L2**.
3. SubPatternAtom.fwd/bck_code → PikeVM instructions (published fix never touches) — **L3**.
4. MetaValue::String literal → metadata accessor (published far site) — **L4**.
5. SubPattern::*ChainTail.chained_to → chain verification. Screener lead. Rejected: every use is
   gated by a HashMap lookup keyed by the same id, and keys can only be in-range head ids, so an
   out-of-range value is never fed to `get_sub_pattern`. Not reachable — recorded, not shipped.
6. re_code bytecode *content* (in-range location, malformed instruction stream) → InstrParser
   `get_unchecked`. Rejected: proving arbitrary bytecode well-formedness is not a fair 45-minute
   fix, and the property would then require reimplementing the compiler.
7. compiled_wasm_mod → wasmtime `Module::deserialize` (native-code-serialization feature, disabled
   by default). Rejected: feature-gated, not on the default path; out of scope.
8. RuleInfo / tag / metadata IdentIds and LiteralIds → `.unwrap()` panics (safe crashes, not UB).
   Not shipped as a lever; the oracle validates them defensively.
9. RuleId from the deserialized WASM module → scanner host functions. Rejected: needs a crafted
   WASM module, not a fair data-only blob lever; noted as out of scope.
10. serialized_globals bincode decode `.expect()` → panic on malformed globals (safe crash). Not a
    memory-safety lever; oracle ignores.

Injected siblings considered:
A. **is_fast_scan `get_unchecked`** — chosen (L5): independent bit vector whose length the blob
   controls, reachable only in the fast-scan path, plausible perf edit.
B. **BStringPool `get_bytes` unchecked unwrap at the scanner call site** — chosen (L6): plausible
   hot-path edit; the blob controls the literal id through SubPattern values.
C. `atoms.get_unchecked(atom_idx)` — already exists upstream and the index comes from the AC
   automaton built from the same atoms; not attacker-independent. Rejected.
D. A parallel unchecked rules-by-RuleId lookup — reachable only from WASM-supplied ids. Rejected
   with 9.
E. New derived lookup table added to Rules — too intrusive/unrealistic for a sibling. Rejected.

Why the picks beat the others: L1, L2, L3, L5, L6 each need the mechanism (which table, which id,
what the bound really is) rather than a search; each sits in a different module and has a distinct
dismissal. L4 is the published far site (separate accessor layer, invariant produced elsewhere).

## Sites / routes / input shapes the security tests cover

- S1 atom id == sub_patterns.len() (L1) via `Rules::deserialize`.
- S2 `deserialize_from` (reader form) with the same class of inconsistency (entry-point form).
- S3 anchored id out of range (L2).
- S4 fwd_code beyond re_code (L3).
- S5 MetaValue::String literal is invalid UTF-8 (L4).
- S6 pattern id beyond fast_scan_patterns but within num_patterns (L5).
- S7 SubPattern literal id beyond the literal pool (L6).

Every test asserts: the conversion returns `Err` (a clean client error) and no panic. On the pinned
tree each returns `Ok` and the test fails.

## Coupled must-keep-working (functional tests)

- plain literal rule round-trip → scan match (L1).
- rule with no atoms (`condition: true`) round-trips (L1 boundary).
- anchored literal (`at 0`) round-trip → match (L2).
- regexp pattern round-trip → match (L3).
- string metadata stays `MetaValue::String`; raw-bytes metadata with non-UTF-8 stays
  `MetaValue::Bytes`; binary/hex patterns still scan (L4/L6).
- legitimate fast-scan mode on a compiled rule set finds matches (L5).
- `deserialize_from` of a valid serialized blob works end to end.
- the project's own serialization test (restored pristine at grade time).

## Oracle (solution/fix.patch)

Post-decode validation in `Rules::deserialize`, before `build_ac_automaton`:
- atoms: sub_pattern_id < sub_patterns.len();
- anchored_sub_patterns: each id < sub_patterns.len();
- sub_patterns: each pattern id < num_patterns and `fast_scan_patterns.len() == num_patterns`;
- SubPattern nested ids: chained_to < sub_patterns.len(); literal/Base64 alphabet ids exist in the
  pool;
- atoms: fwd/bck code location < re_code.len();
- metadata: `MetaValue::String` literal exists and is valid UTF-8 (Bytes untouched).
Plus the published `SubPatternId: Ord` derive is not needed (use `all`).

## Risks / open questions (verify in the container)

- Whether `fwd_code` is `Some` for the regexp used by the attack and whether the pinned scanner
  actually reaches the VM with an out-of-range location.
- Whether the injected fast-scan attack reaches `is_fast_scan` (needs fast_scan(true), a matching
  atom, and the wasm bitmap sized by `num_patterns`).
- Whether the injected literal-pool attack reaches the pool lookup with a matching atom.
- Build time / offline rebuild cost of the wasmtime-heavy workspace.
