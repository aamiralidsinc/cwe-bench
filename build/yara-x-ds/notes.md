# yara-x-ds — build notes

Start (UTC): 2026-10-24T02:45:31Z (pipeline start)
End (UTC): 2026-10-24T04:04:53Z

## Candidate
virustotal/yara-x, GHSA-2JX3-FF3V-J7JJ, CWE-502. Pinned 4fbaf55606e06af6e109d02b764a9190edf8c4ed,
published fix 25efa375572efcfbe880a263ee3b0932d4b61a24 (the next commit). Pattern A+B, injected track.

## What the flaw is (one line each)
`Rules::deserialize` bincode-decodes a caller-supplied blob and trusts it; scanning and the metadata
accessor later use the decoded ids/offsets/string bytes in unchecked (`get_unchecked`, `to_str_unchecked`)
operations. The published fix checks only the atom sub-pattern ids (off by one) and turns the metadata
UB into a panic.

## The security property (written once)
A blob inconsistent with what the compiler produces (an index/offset out of range, a text literal that
is not valid UTF-8, a per-pattern table that does not cover every pattern) must be refused by the
restore API with an error; it must never be accepted and used. Every lever below is the same property
read over one more piece of compiler-produced data. The instruction never names a route or site.

## Levers (main first)
1. **L1 atom-id boundary (MAIN, HOW = shape a plausible check mishandles).** `atoms[i].sub_pattern_id`
   may equal `sub_patterns.len()`; the obvious/published shape `len < max_id` accepts exactly that
   value. Test: id == len. reason to dismiss: the boundary relation "largest valid index" vs "length";
   a check copied from the upstream shape or written as `id > len` looks finished.
2. **L2 anchored ids (HOW = route where protection never existed).** `anchored_sub_patterns` ids go to
   the same unchecked `get_sub_pattern` in the scanner, but the published check only scans atoms.
   real, unmodified upstream code. reason to dismiss: anchored patterns are a separate optimisation
   path that never touches the Aho-Corasick atoms the report/fix talk about.
3. **L3 chain ids (HOW = route where protection never existed).** `chained_to` inside
   `SubPattern::*ChainTail` values is followed with unchecked `get_sub_pattern`. real upstream.
   reason to dismiss: it is an id nested inside an enum value, and chains look like a neighbouring
   feature rather than the id vectors.
4. **L4 text-metadata UTF-8 (HOW = producer off the check's path + far site).** The UTF-8 invariant of a
   `MetaValue::String` literal is established only by the compiler; the deserializer never checks it and
   the model accessor asserts it with `to_str_unchecked`. The published fix only turns it into a panic
   at read time; the property requires refusal at restore. reason to dismiss: a read-only accessor in a
   different module whose own comment says the string is surely valid.
5. **L5 regex code locations (HOW = route where protection never existed).** atom `fwd_code`/`bck_code`
   index `re_code` with `get_unchecked` in the Pike/Fast VMs; the published fix does not look at them.
   real upstream. reason to dismiss: regex bytecode validity reads as a compiler invariant and the VM
   is a separate engine package.
6. **L6 injected: `is_fast_scan` bit-vector (HOW = route where protection never existed).** The sibling
   rewrites the existing safe indexing of `fast_scan_patterns` as a `get_unchecked` hot-path read.
   reason to dismiss: a derived performance cache, not compiled rule data.
7. **L7 injected: dense `filesize_bounds` table (HOW = producer off the check's path).** The sibling
   replaces the pattern→bounds map with a dense `Vec<Option<..>>` read through `get_unchecked`; only
   `Compiler::build` pads it to one entry per pattern, and the deserializer never calls the producer.
   reason to dismiss: a table of optional bounds looks naturally sparse, so a short table reads as
   normal.

## Full candidate list (all sites found; why each was picked or dropped)
- atoms.sub_pattern_id -> get_sub_pattern — reported route; kept as baseline + L1 boundary shape.
- anchored_sub_patterns -> get_sub_pattern (scanner/context.rs) — PICKED (L2), real upstream.
- chained_to in chain tails -> get_sub_pattern (scanner + chain verifier) — PICKED (L3), real upstream.
- metadata MetaValue::String -> to_str_unchecked (models.rs) — PICKED (L4), published far site,
  upstream only degrades it to a panic.
- fwd_code/bck_code -> re_code get_unchecked (pikevm/instr) — PICKED (L5), real upstream.
- compiled_wasm_mod -> wasmtime Module::deserialize — DROPPED: needs the off-by-default
  native-code-serialization feature and an opaque crafted module, so no fair behavioural test.
- published off-by-one — folded into L1 as its shape.
- atoms.get_unchecked(atom_idx) — DROPPED: atom_idx comes from the AC automaton built from the same
  atoms at load; self-consistent.
- teddy internal unchecked indices — DROPPED: rebuilt from atoms at load; self-consistent.
- pikevm split ids / InstrParser class ranges — DROPPED as separate routes: they are reachable only
  from re_code contents plus a code location, so the tested shape is the location check (L5); requiring
  full bytecode validation would not be fair.
- literal/regex/ident ids behind `.get(..).unwrap()` — NOT a route: a checked lookup panics, no UB;
  the property targets unchecked access and invalid text.
- num_patterns used to size the wasm bitmap — NOT a route: the slice is checked (panic, not UB).
- rules Vec indexed by a wasm-supplied RuleId — DROPPED: not structurally checkable from the blob
  (the wasm module is opaque), so it cannot be a fair lever.
- fast_scan_patterns bit vector — INJECTED sibling (L6), realistic hot-path micro-optimisation.
- filesize_bounds map -> dense vec — INJECTED sibling (L7), realistic hot-path micro-optimisation;
  header_constraints would be the same class, so only one such table was added.

## Sites / entry points covered by the security tests
`Rules::deserialize` (public Rust API; `deserialize_from` delegates to it) is the restore entry point the
tests drive. Every route above is reached after a successful restore by `Scanner::scan` or
`Rule::metadata`; the tests assert the restore itself refuses the blob (no UB execution needed).

## Coupled must-keep-working (functional)
- serialize -> deserialize -> scan identical results for a corpus (literal/regex/hex, tags, private and
  global rules, several namespaces);
- rules with no patterns at all (empty atoms/sub-patterns/num_patterns);
- anchored-only rules (`$a at 0`, `$b in (..)`);
- chained patterns (hex `{ .. [0-1000] .. }`);
- every metadata kind round-trips, in particular raw-byte metadata whose bytes are not valid UTF-8
  must stay `Bytes` (an over-broad "all literal bytes must be UTF-8" fix fails this) and text metadata
  must stay text;
- the project's own `compiler::tests::serialization` test.

## Injected siblings
L6 `Rules::is_fast_scan` unchecked bit-vector read; L7 `filesize_bounds` dense vector read. Both are
maintainer-plausible hot-path optimisations, applied in `injection.patch`, reached through the real
restore+scan path, covered only by the general property, and far from the published fix hunks.

## Test mechanics
Hidden tests are Rust unit-test modules copied at grade time into `lib/src/compiler/tests/` (the crate's
existing unit-test area) and declared by appending two `mod` lines; they build a legitimate `Rules` with
the public compiler, mutate the in-memory compiled structure, `serialize()` it, and assert
`Rules::deserialize` refuses the resulting blob. Functional tests use only the public API. The verifier
runs the native libtest target offline through a small log->JUnit converter.

## Verified / not verified
(to fill after the gate)

## Verification (local, before the gate)

Pinned+injected tree (the agent's starting point): 9/9 security tests fail, 7/7 functional tests pass.
Reference fix: 16/16 hidden tests pass; the project's own lib target is 323/323 green (307 project
tests + 16 hidden). The published fix alone: only `atom_sub_pattern_id_beyond_count_is_refused`
passes; the boundary value, anchored, chain, metadata-at-restore, regex locations and both injected
tables are still accepted, which is the intended gap.

Wrong-fix patches, each run against the hidden tests (security failures / functional failures):
sf_atom_boundary 1/0, sf_no_anchored 1/0, sf_no_chain 1/0, sf_no_metadata 1/0, sf_no_code_loc 2/0,
sf_no_fast_scan 1/0, sf_no_filesize 1/0, sf_atoms_only 7/0, sf_crash 9/0, sf_reads_only 8/0,
sf_fwd_only 1/0, ff_overbroad 0/1, ff_refuse_all 9/7, pass_hardening 0/0, pass_alternative 0/0.

Injection: `environment/injection.patch` applies to the pinned commit and the project's whole lib test
target stays green with it (307/307 before the fix).

## What I could not verify
- The blind pass patch is written later by the harness; not present here.
- Harbor-level nop/oracle/patch runs: see the gate report (below).
- The wasm-module route (`compiled_wasm_mod` passed to wasmtime's deserialize) was left out: it needs
  the off-by-default native-code-serialization feature and an opaque crafted module, so there is no
  fair behavioural test. Noted as outside the built scope; no test relies on it.
- Full bytecode validation of `re_code` (malformed instruction streams at an in-range location) is a
  larger compiler-consistency problem; the task tests only the out-of-range location, which is fair.
- `Rules::get` indexed by a RuleId that comes from the (attacker-controlled) wasm module is not
  structurally checkable from the blob, so it is not a lever.

## Images
- environment image builds (rust:1.91-slim-bookworm, pinned checkout + injection, warm target); a
  container from it runs `cargo test --offline` as the uid-1000 user and the project's
  `compiler::tests::serialization` passes offline with the injected tree.
- verifier image builds with the offline crate cache and a warm /opt/target.

## Gate
- static: PASSED (2026-10-24T03:11Z).
- nop: PASSED (03:18Z) - 9/9 security tests fail on the pinned+injected verifier, 8/8 functional
  tests pass (7 hidden + the project's compiler::tests::serialization), reward 0.0.
- oracle: PASSED (03:27Z) - 3/3 runs reward 1.0, identical security (9/9) and functional (8/8).
- patches: PASSED (04:05Z) - 15/15 behaved as declared: the seven per-lever security_fail patches
  each leave exactly their lever's test(s) failing with all functional tests passing (1,1,1,1,2,1,1
  security failures), sf_atoms_only leaves 7, sf_crash 9, sf_reads_only 8, sf_fwd_only 1;
  ff_overbroad (rejecting raw byte metadata) and ff_refuse_all break functional tests; hardening and
  alternative both score 1.0. blind.patch written later by the pipeline, so it was skipped.
