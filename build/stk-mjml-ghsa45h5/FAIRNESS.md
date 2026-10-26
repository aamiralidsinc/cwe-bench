# FAIRNESS — stk-mjml-ghsa45h5

P1 = "No file outside the include base is ever read while a document is processed, and nothing
taken from such a file may reach a result the product produces or a dependency set it maintains.
This holds however the target is written and at every depth of nesting."
P2 = "When an include cannot be read or is refused, everything the product reports names the target
only as the template wrote it. No resolved filesystem location of the target or of the including
document may appear in compiled output, in reports, or in command-line output."

## 1. Test fairness

| test (file::name) | what it asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| security/01::a relative path that climbs out of the root is refused | no outside marker in html/diagnostics, resolved target absent from html, target never read | P1 "No file outside the include base is ever read … however the target is written" | no; only a guard that never looks at the resolved file fails | low |
| security/01::an absolute path outside the root is refused | same | P1 "however the target is written" | no | low |
| security/01::a sibling directory sharing the root prefix is refused | same | P1 (target is outside the base) | no; a bare `startsWith(base)` guard is wrong, not correct | low |
| security/01::a link inside the root that points outside is refused | same, for a symlink whose physical file is outside | P1 (the *file* read is outside); Preservation "a link that stays inside the base keeps working" implies the converse | no; a lexical guard reads an outside file, so it is not correct. **Shape reading is a judgment call** | medium |
| security/02::the parser package refuses an out-of-root target | parser API returns no outside content and never reads it | P1 unqualified ("a document is processed"); the parser package is a published entry point of the repo | no; a guard only in mjml-core is the catalogued `sf_core_only` wrong fix | medium |
| security/02::the parser defaults its root to the working directory | parser with `{}`, cwd = project, refuses and never reads the outside target | base rule "Otherwise the working directory is the base" | no | low |
| security/02::the command-line validation path refuses an out-of-root target | `-v` exits non-zero, no marker, no read | P1 + Contract "reported as an ordinary document or validation error. The run does not crash" (an ordinary reported validation error already yields a non-zero `-v`) | no; a silent drop is not a reported refusal | medium |
| security/02::the command-line render path refuses an out-of-root target | `-s` stdout has no marker | P1; System "…by the command-line tool" | no | low |
| security/03::a partial can not climb out of the root with a relative include | no marker/target in output or diagnostics, no read | P1 "at every depth of nesting" | no | low |
| security/03::a deeper partial does not gain a wider root | same at depth 3 | P1 "at every depth of nesting" | no; re-rooting at each partial is wrong (functional/01 nested test catches it) | low |
| security/04::watch mode does not open a file outside the root | watcher process never opens the outside suffixed target | P1 "…or a dependency set it maintains" | no; fixing only the parser is the catalogued `miss_watcher` wrong fix | medium |
| security/05::a missing target inside the root is not located in the output | no resolved path; `./missing.mjml` still named | P2 "names the target only as the template wrote it"; Preservation "still reported with the target as written" | no; printing only a basename breaks "as written" | low |
| security/05::a missing target outside the root is not located in the output | no resolved path | P2 "No resolved filesystem location of the target…" | no | low |
| security/05::the validation report does not locate a missing target | CLI `-v` output: no resolved path, written name present | P2 "in reports"; Preservation | no | low |
| security/05::the command-line render does not locate a missing target outside the root | CLI stdout/stderr: no resolved path | P2 "in command-line output" | no | low |
| functional/01::an include inside the root is rendered | inside marker in html | Preservation "includes inside the base render" | no | low |
| functional/01::a configured partials directory is the root | filePath=partials wins over the document dir | base rule 1 + "a configured partials directory takes precedence over the document's own directory" | no | low |
| functional/01::a configured root given as a file uses its directory | base = dirname of the file-valued option | base rule "A configured value that names a file contributes its directory" | no | low |
| functional/01::with no configured root the working directory is the root | cwd base resolves inside include | base rule "Otherwise the working directory is the base" | no | low |
| functional/01::a partial with another extension keeps working | `.txt` partial renders | Preservation "a partial with any extension keeps working" | no; restricting to `.mjml` is not correct | low |
| functional/01::a link inside the root that stays inside keeps working | inner symlink renders | Preservation "a link that stays inside the base keeps working" | no | low |
| functional/01::a nested partial resolves a relative include from its own location | `sub/child.mjml` reaches `../ok.mjml` in the base | base rule "A partial may still reach another file inside the base, including one above its own directory"; Preservation "nesting resolves relative to the including partial" | no | low |
| functional/01::a missing include inside the root still reports an error naming the target as written | `./missing.mjml` in output/messages | Preservation "still reported with the target as written and the enclosing line" | no | low |
| functional/01::includes can still be ignored without touching the filesystem | `ignoreIncludes` reads nothing | Preservation "an option that skips include processing still leaves the filesystem untouched"; P1 | no | low |
| functional/02::changing an in-root partial recompiles the template that includes it | edit to in-base partial triggers recompile | Preservation "a change to a partial inside the base still leads to the documents that depend on it being rebuilt" | no | low |
| functional/03::the parser package suite passes | upstream suite green | "Everything that works today keeps working"; "Keep every legitimate use working" | no (reference passes) | low |
| functional/03::the core package suite passes | upstream suite green | same | no (reference passes) | low |

## 2. Leniency (quality, non-blocking)

| property / trap | most plausible wrong fix | caught? |
|---|---|---|
| P1 / T1 (parser confinement) | guard only in the high-level API (`checks/sf_core_only.patch`) | yes — security/02 parser-package and validation tests |
| P1 / T1 | lexical containment without resolving links (`checks/sf_lexical.patch`) | yes — security/01::link (only that test) |
| P1 / T6 (base carried through recursion) | refuse every `..`, or re-root at the partial's own directory | yes — functional/01::nested; configured-root tests; `ff_refuse_all` fails 10 functional |
| P1 / T4 (watch resolver) | confine the parser only (`checks/miss_watcher.patch`) | yes — security/04 |
| P2 / T7 (disclosure) | scrub the compiler comment only, or the validator only (`checks/miss_diagnostics.patch`, `upstream_fix`) | yes — security/05 in-root-missing and validation-report tests |
| P2 (refusal diagnostics) | denial message prints the resolved target | yes — security/05::outside-missing and CLI-render tests exercise the denial path |

Wrong fixes **no test catches**:
- Scrubbing only the *target's* path while `ruleError`'s prefix keeps the **including document's**
  absolute path (`Line N of /abs/page.mjml`). P2's second sentence forbids it; every assertion only
  compares the target's resolved path.
- The circular-inclusion error still prints `Circular inclusion detected on file : ${partialPath}`;
  no test drives a circular include (the reference fixed it, a solver need not).
- A lexical (non-`realpath`) guard in the **watch** resolver: the watch fixture has no symlink.
- `fsprobe.cjs` does not hook `fs.promises.*`; a read through the promises API would not be seen.

## 3. Hints (quality) and 3a. Required: generalize

Quotes that are surface descriptions rather than general properties (see "Required: generalize" in
the verdict block): the API/CLI channel sentence; "or a dependency set it maintains"; the
rebuild-on-change clause; the include-skipping-option clause; "a link that stays inside the base
keeps working"; "including one above its own directory"; the title/impact's "project's partials
directory". Hint-only wording (quality): "however the target is written and at every depth of
nesting" (variant list), "Fix the flaw and its close variants, not just the example shown" (variant
list, and no example is actually shown), "nesting resolves relative to the including partial"
(mechanism), "a configured partials directory takes precedence over the document's own directory"
(duplicates the base rules).

## 4. Realism

All traps are real code a maintainer wrote: T1 is the parser's own include handler; T6 is the
documented configured-directory/nested behaviour; T4 (`fileContext.js`) and T7
(`errorAttr.js`/`ruleError.js`) are unmodified upstream paths that the published fixes leave open —
realistic by definition, never "out of scope". The `watch-only` suffixed fixture is a harness
construction around real `ensureIncludeIsMJMLFile` behaviour, not a planted defect. No contrived or
unreachable trap found. `checks/pass_alt.patch` appears content-identical to `solution/fix.patch`,
so the declared second design is not actually exercised.

## Stacking checks

| check | C1 (T1+T6) | C2 (T4) | C3 (T7) |
|---|---|---|---|
| S1 coupled traps | keep-working clauses ("includes inside the base render", "nesting resolves…", "a link that stays inside…", all base/extension rules) are stated; none contradicts P1 — every kept target resolves inside | functional/02's rebuild value is stated; contradicts nothing (read outside, rebuilt partial inside) | functional/01's "target as written" value is stated in Preservation and agrees with P2 |
| S2 shape traps | all refused shapes (`../`, absolute, `project-sibling`, link-out, deep climbs) resolve outside the base; no refused shape lies in the stated legitimate set | `../secret/watch-only` is outside; the in-root partial is legitimate | missing targets: in-base (legitimate, must name as written) vs outside (refused) |
| S3 fixtures/harness | fixture dirs and symlinks are legitimate fs states; driven via `mjml2html`, `MJMLParser`, CLI `-s`/`-v` | real `-w` and `fileContext`; in-root partial legitimate | `mjml2html`, `-v`, `-s` |
| S4 independence | pinned fails all C1 tests through their own routes; `miss_parser` still passes the 5 non-C1 tests | `miss_watcher` fails only the watch test (14/15) | `miss_diagnostics` fails only the 2 disclosure tests (13/15) |
| S5 history (H3a) | `upstream_first_fix.patch` (fix A alone) still reads outside targets → violates P1 literally; gate score 0/15 | not covered by A; real uncovered upstream route | not covered by A; real uncovered upstream route |
| S6 contracts | only existing names (`filePath`, `actualPath`, `MJMLParser`, CLI flags); protected object = "the include base", product terms | "a dependency set it maintains" names the object; no new interface | outcome stated; no authority |
| S7 decisive tests | — | — | — |

S7: six runs (3 deepseek, 3 mimo) all scored 0.9333 with 0 functional failures — exactly **one**
security test decided every run. Per-run `results.json` is outside `build/`, so the deciding test is
not named in the build artifacts; the most plausible is the watch test (the route both the notes and
the manifest flag as dismissible).

## Verdict

**READY.** Every correct fix that follows the primary mechanism — resolve the include base, refuse a
target that resolves outside it before the read, carry the base through the recursive parse, and
report the target as written — passes all 27 tests: the reference and the hardened variant score
1.0 (the blind patch was never produced — `blind_status.txt` reports an extraction error — so it
proves nothing). The four "medium" rows rest on unlisted routes/layers, but P1/P2 read literally
cover each of them, and each remaining failure only occurs for a fix that is *not* correct (reads an
outside file, silently drops a refusal, guards only one layer). No contradiction between instruction
and tests; no undeclared name or error class is needed. Nothing in gate a rests on leniency, hints or
realism, which are listed below for tightening only.

**Required: generalize**
- "The same documents are processed by the library API and by the command-line tool." → "Include
  processing is part of the product's normal behaviour, wherever documents are processed."
- "…or a dependency set it maintains" → "…or any state the product derives from it."
- "a change to a partial inside the base still leads to the documents that depend on it being
  rebuilt" → delete; the general "Everything that works today keeps working" covers it.
- "an option that skips include processing still leaves the filesystem untouched" → delete; P1
  already covers not reading.
- "a link that stays inside the base keeps working" → "a target that resolves inside the base keeps
  working."
- "including one above its own directory" → "A partial may still reach any file inside the base."
- Title/impact "the project's partials directory" / "the project the template belongs to" → "the
  include base."

**Quality to tighten**
- Add an assertion that the **including document's** resolved path never appears (P2 sentence 2 is
  currently untested).
- Add a circular-include case; the resolved path in that message is currently untested.
- Add a symlink-out fixture to the watch test (a lexical watcher guard passes today).
- Hook `fs.promises.*` in `fsprobe.cjs`.
- Reword "however the target is written and at every depth of nesting" → "without exception"; "Fix
  the flaw and its close variants, not just the example shown" → "Fix every way the property can be
  violated"; drop the duplicated precedence clause.
- Replace or genuinely vary `checks/pass_alt.patch` (identical to the reference).
- Tighten the 500 ms post-compile wait in security/04.

Human review: confirm which single security test decided the six 0.9333 runs (most plausibly security/04::watch mode does not open a file outside the root), and that the parser-package route (security/02 #5) and the `-v` non-zero status (#7) are within the stated property.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
