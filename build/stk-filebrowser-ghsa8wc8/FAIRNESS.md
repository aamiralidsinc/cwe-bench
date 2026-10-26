# FAIRNESS review — stk-filebrowser-ghsa8wc8

Scope read: `instruction.md`; `tests/{test.sh,score.py,Dockerfile,support/zzscope_support_test.go,security/zz_sec_scope_test.go,functional/zz_func_scope_test.go}`; `solution/fix.patch`; `manifest.json`; `notes.md`; all 13 `checks/*.patch`; `gate_report*.json`; `trial_detail_{deepseek,mimo}.json`. No trial_summary.md exists.

Harness: every hidden test drives the product's own `handle()` wrapper with a bolt-backed user whose `Fs` is built by `users.Clean`, a real settings key and a signed JWT. The role is genuinely restricted (`Scope: "/user"`, `Root: <tmp>/root`), and the escaping links are planted inside the scope by the test (the instruction's own precondition).

## 1. Per-test fairness

| test (file::name) | what it asserts | covering instruction sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security::TestSec_DanglingLinkUploadPost | POST `/evil?override=true` through a dangling link to outside → 4xx and target absent | "No path an account supplies, and no path the product derives from it, may cause anything outside that account's folder to be created … however the path is written, whichever intermediate links it passes through"; "must fail with a client error" | no | low |
| security::TestSec_DanglingLinkTusCreate | same escape on the resumable-create endpoint → 4xx, target absent | same clause; route-agnostic ("anything … created") | no | low |
| security::TestSec_DanglingLinkTargetThroughSymlinkedComponent | absolute target with `..` after a symlinked component → 4xx, target absent | same clause, "however those links are written or where they ultimately point" | no | low |
| security::TestSec_DanglingLinkRelativeTargetThroughSymlinkedComponent | relative target with `..` after a symlinked component → 4xx, target absent | same clause (covers relative spelling) | no | low |
| security::TestSec_MkdirThroughEscapingLink | POST `/linkdir/newdir/` through an existing escaping dir link → 4xx, `outside/newdir` absent | "created" (a directory is created); refusal clause | no | low |
| security::TestSec_CopyOverwritesThroughEscapingDestinationLink | copy `/src`→`/dst` where `dst/file.txt` is a link to an outside victim → 4xx, victim unchanged | "… moved, copied or otherwise changed"; "must fail with a client error" | no — but only because the refusal is surfaced as a client error, which the instruction states. A refusal folded into a partial-copy aggregate that maps to 5xx would fail, and that is a stated-requirement violation, not a test artifact | low |
| security::TestSec_RecursiveListingThroughEscapingLink | GET `/link/sub` (root reached through an escaping link) emits no out-of-scope name; if 2xx, body lacks "sub" | "No account may learn anything about anything outside its folder — content, names, sizes or times — through any operation it performs" | no — the body is a bare entry array; emitting the root entry would itself disclose out-of-scope metadata. Residual: a fix that echoes the *requested* path in a 2xx body (the user supplied it) would trip the "sub" substring; not something a containment fix does | low |
| functional::TestFunc_CreateNewFile | POST a new nested file inside the scope → 2xx, file created | "Creating a genuinely new file or folder inside the folder keeps working" | no | low |
| functional::TestFunc_OverwriteThroughInScopeLink | POST to a link resolving inside the scope → 2xx, target rewritten | "Overwriting a file that already exists inside the folder keeps working, including when it is reached through a link that resolves inside the folder" | no (refusing all links fails, but that contradicts this bullet) | low |
| functional::TestFunc_DanglingLinkToInScopeTarget | POST through a dangling link whose target is inside → 2xx, file created | "… including through a link whose target is inside the folder and does not exist yet" | no | low |
| functional::TestFunc_Mkdir | POST `/one/two/` → 2xx, directory created | "Creating a genuinely new file or folder inside the folder keeps working" | no | low |
| functional::TestFunc_MkdirThroughInScopeLink | POST `/linkdir/newdir/`, link resolves inside → 2xx, dir created | same bullet + "Every other legitimate operation on paths inside the folder keeps working exactly as today" | no | low |
| functional::TestFunc_CopyDirectory | copy a directory in-scope → 2xx, both children copied | "Every other legitimate operation on paths inside the folder keeps working exactly as today" | no | low |
| functional::TestFunc_CopyThroughInScopeDestinationLink | copy with override into a `dst/file.txt` link resolving in-scope → 2xx, in-scope link target rewritten | "Overwriting … including when it is reached through a link that resolves inside the folder" | no | low |
| functional::TestFunc_RecursiveListing | recursive listing of an in-scope tree includes `leaf.txt` | "Listing inside the folder keeps working" | no | low |
| functional::TestFunc_RecursiveListingThroughInScopeLink | GET `/link/sub`, link resolves inside → 2xx, includes `leaf.txt` | "… including when a link inside it points to another place inside it" | no | low |
| functional::TestFunc_TusCreate | resumable create of `/upload.bin` → 2xx, file created | "Every other legitimate operation on paths inside the folder keeps working exactly as today" | no | low |
| functional/project.xml (55 project tests, `go test ./files ./fileutils ./http`) | existing behaviour, incl. `TestCopyAllowsInScopeSymlink`, `TestWithinScope` root-scope, share symlink tests | "Every other legitimate operation … exactly as today"; "An account whose folder is the whole server keeps its current unrestricted behaviour" | no — but a fix that deletes `files.WithinScope` must update the visible `files/file_test.go` (as upstream A did) or the package stops compiling | low/medium |

No row is "yes"; no row leaves a "maybe" unresolved.

## 2. Leniency (QUALITY, non-blocking)

| property / trap | most plausible WRONG fix | caught by | check patch |
|---|---|---|---|
| T1 resolver | one `Readlink` + lexical `Join` + prefix test | all four T1 tests | `miss_resolver.patch` (fails exactly those four) |
| T1 resolver | `EvalSymlinks` with lexical walk-up on `ENOENT` (upstream A) | the four T1 tests (+copy) | `upstream_first_fix.patch` (5 fail) |
| T3 mkdir | guard only the file-upload branch | `TestSec_MkdirThroughEscapingLink` | `miss_mkdir.patch` |
| T3 mkdir | check the wrong path (`"/"`) | same | `wrong_resource.patch` |
| T3 mkdir | create first, refuse after | same (`zzRequireNoFile`) | `check_after_adjustment.patch` |
| T3 mkdir | refuse by returning an internal error | same (needs 4xx) | `crash_as_refusal.patch` |
| T4 copy | guard source + top-level destination only | `TestSec_CopyOverwritesThroughEscapingDestinationLink` | `miss_copy.patch` |
| T5 listing | filter content reads only, not the walk root/entries | `TestSec_RecursiveListingThroughEscapingLink` | `miss_recursive.patch` |
| "no outside change" | refuse everything / refuse every link | all 10 functional tests + project tests | `refuse_all.patch`, `overbroad_symlink.patch` |

Wrong fixes **no test catches**:
- **move/rename** left unguarded — the property says "moved"; no test drives `action=move`/rename.
- **delete/RemoveAll** through an escaping link left unguarded — "otherwise changed"; no hidden test drives delete (`hardening.patch` adds the guard, nothing exercises it).
- **create-then-refuse on the upload route**: `MkdirAll` of an out-of-scope parent before the refusal. `zzRequireNoFile` checks only the final target, and every fixture's target sits directly in an existing directory.
- **disclosure on the non-recursive read/listing route** (plain GET/list, raw download); only the recursive route and the share routes are exercised.
- **chmod/chtimes** outside the folder — covered by the property, not by any test.

## 3. Hints (QUALITY, non-blocking)

- "then upload to the link's path" — names the reported entry point. Neutral: "then write to the link's path".
- "Fix the problem and its close variants." — paraphrases a variant count ("its close variants" tells the solver more sites exist). Neutral: "Make the invariants above hold."
- "These are invariants, not a list of cases. The example above is an example." + "Do not special-case the example above." — twice nudges the solver to hunt variants. Keep only "These are invariants, not a list of cases." and drop the other two.
- The `..`-after-a-link wording ("however those links are written or where they ultimately point") is a general property, not a mechanism hint; keep it — it is what makes the two `..` tests fair.

## 3a. Surface descriptions — Required: generalize

1. "then upload to the link's path" → "then write to the link's path".
2. The per-operation keep-working bullets — "Creating a genuinely new file or folder inside the folder keeps working, including through a link whose target is inside the folder and does not exist yet." / "Overwriting a file that already exists inside the folder keeps working, including when it is reached through a link that resolves inside the folder." / "Listing inside the folder keeps working, including when a link inside it points to another place inside it." — enumerate create/overwrite/list, i.e. test routes. Replace the three with one property: **"Every legitimate operation on a path that resolves inside the folder keeps working exactly as today — including a path that does not exist yet, and a path that passes through a link whose target is inside the folder."** (This keeps `TestFunc_DanglingLinkToInScopeTarget` fair.)
3. (minor) "that account may create, overwrite, move and browse only inside the folder" — an operation list; neutral: "that account may act only inside the folder".

## 4. Realism (QUALITY, non-blocking)

All four traps are the pinned tree's own unmodified code, reachable through the real handlers: the pinned `WithinScope` comment literally says a dangling link "resolves to its parent and is therefore allowed" (T1); the POST directory branch, the per-child copy destination and the recursive walk never consult containment and are untouched by both published fixes (T3/T4/T5). Nothing looks planted. The reference is a call-site design rather than upstream's `ScopedFs` refactor; that is a solution choice, not a contrived trap, and it is what keeps T3/T4/T5 independent. Minor build note: `manifest.patch_checks` lists `blind.patch`, which is absent from `checks/`; the patches stage ran 13/13 without it.

## Stacking checks

| check | concept | result |
|---|---|---|
| S1 coupled traps | T1 | `TestFunc_CreateNewFile`/`_OverwriteThroughInScopeLink`/`_DanglingLinkToInScopeTarget`/`_TusCreate` vs "created/overwritten … only inside the folder": no contradiction (every allowed value resolves inside). |
| S1 | T3 | `TestFunc_Mkdir`/`_MkdirThroughInScopeLink`: creating inside stays allowed by the very property that forbids creating outside. No contradiction. |
| S1 | T4 | `TestFunc_CopyDirectory`/`_CopyThroughInScopeDestinationLink`: "keeps working exactly as today" vs "copied" — the forbidden copy is only the escaping one. No contradiction. |
| S1 | T5 | `TestFunc_RecursiveListing`/`_RecursiveListingThroughInScopeLink`: the disclosure rule forbids learning about *outside*; the kept value is inside. No contradiction. |
| S2 shapes | T1 | Refused: dangling link, absolute/relative target, `..` after a link — all resolve outside; the legitimate set is "resolves inside", which is what the functional fixtures use. Outside. |
| S2 | T3 | Refused form `/linkdir/newdir/` is the same trailing-slash form `TestFunc_Mkdir` accepts; only the escaping link is illegitimate. |
| S2 | T4 | Refused shape is a destination-tree link to outside; the accepted shape (`TestFunc_CopyThroughInScopeDestinationLink`) is the same link resolving inside. |
| S2 | T5 | Refused root `/link/sub` resolves outside; the same path resolving inside is accepted. |
| S3 fixtures | all | Escaping links inside the scope are the instruction's stated precondition; user is enabled (Create/Modify as needed) and authenticated; root/scope are real. |
| S3 harness | all | Real `handle()` + the four mounted handlers + `users.Clean`-built Fs. A handler-level and a filesystem-level fix both score 1.0 (`alternative.patch`). Only mux registration in `router.go` is bypassed — not a layer at which this bug can be completely fixed (the copy destination is not in the URL). |
| S4 independence | T1/T3/T4/T5 | `miss_resolver` fails only T1's four; `miss_{mkdir,copy,recursive}` fail only their own test (gate report). H3c masking: nop stage — 7/7 security tests fail on pinned code through their own routes. |
| S5 history | H3a | `upstream_first_fix.patch` violates the property read literally, not merely differently: its `within()` still walks up to the link's lexical parent, so a dangling escaping link is written through (and the `..` shapes too). Gate: it fails 5 security tests with functional green. No widening needed. |
| S6 contracts | all | Tests use only existing package identifiers (`handle`, `handleFunc`, `authToken`, `userInfo`, `newMemoryUploadCache`, the four handler constructors) — no guessing, but renaming them would break compilation. No wrong-object trap, no fail-open authority (containment is decided from the filesystem). |
| S7 decisive tests | all | No `trial_summary.md`. `trial_detail_*.json`: five runs at 0.8571 (=6/7 security, functional green), one at 0.7143 (=5/7). Per-test outcomes are not in `build/` and the trial dirs are outside the review root, so the decisive test cannot be named here; the arithmetic says a single security test decided each 0.8571 run. Most likely `TestSec_CopyOverwritesThroughEscapingDestinationLink` (an FS-layer fix that aggregates the copy refusal into a 5xx) or `TestSec_MkdirThroughEscapingLink` (the only test every near-miss check patch fails). Both were re-checked under S1–S6 and are covered by stated instruction sentences. |

## Verdict

**Gate a: READY.** One containment property ("any path an account supplies, and any path the product derives from it"), one disclosure property and one refusal contract cover all seven security routes when read literally — including the absolute, relative and `..`-after-a-link spellings the property names itself. Every keep-working value has a matching sentence. The primary-mechanism fix (`solution/fix.patch`) scores 1.0, and an independent filesystem-layer fix (`checks/alternative.patch`) also scores 1.0, so a guard at another valid layer passes. The sharp edges (4xx rather than 5xx; refuse before creating) are stated demands, not test inventions. No "yes" and no unresolved "maybe" remains.

**Required: generalize** — §3a items 1–3.

**Quality to tighten** (non-blocking): add move and delete security tests (the untested wrong fixes in §2); use a nested target so "create-then-refuse" outside is caught on upload; replace the bare `"sub"` substring with the emitted entry names; drop the two "example" hint sentences; ship or drop `blind.patch`.

**Human review:** confirm which single security test decided the five 0.8571 trials (per-test data is not in `build/`) — candidates `TestSec_CopyOverwritesThroughEscapingDestinationLink` and `TestSec_MkdirThroughEscapingLink`; both were judged fair above, but S7 requires the decisive test to be re-checked first.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
