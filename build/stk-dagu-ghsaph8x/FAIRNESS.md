# Fairness review — stk-dagu-ghsaph8x (pre-trial, stacked H3b, 4 concepts)

Reviewed: instruction.md, all of tests/ (security + functional + four project-test copies + test.sh,
run_security.sh, run_functional.sh, score.py, Dockerfile), solution/fix.patch, manifest.json, notes.md,
all 14 checks/*.patch. Nothing was run. No trial_summary.md exists in build/; trial_detail_*.json
shows 6/6 runs at reward 0.8 (4/5 security).

## 1. Test-by-test fairness

| test (file::name) | what it asserts | fair because (instruction sentence) | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| security/task_confinement_test.go::TestSecReadOutsideDAGsDirectory | GET `..%2Fsecret/spec` → 4xx; marker absent from body; victim file still exists and intact | "The configured DAGs directory is the only place a DAG file may be read …" + "An attempt made through the HTTP API must be refused with a client error and must leave the filesystem unchanged." | no — refusal at the dispatcher or at the store lookup both give 4xx (pass-alt proves the store layer yields 404); refusal form is only "a client error" | low |
| …::TestSecDeleteOutsideDAGsDirectory | DELETE `..%2Fsecret` → 4xx; victim file still exists | same sentence, "… or deleted …" | no (same two valid layers; sf-reads-only is a wrong fix, not a correct one) | low |
| …::TestSecCreateOutsideDAGsDirectory | POST create with body name = absolute path, no spec → 4xx; no file at that path | property + "Creating a DAG with a workflow body and creating one without a body both keep working"; refusal is a client error | no — a fix returning 5xx (sf-crash) is non-compliant with "client error"; handler- or store-layer refusal both work | low |
| …::TestSecRenameOutsideDAGsDirectory | rename destination `..` → 4xx; parent `.yaml` not created; source still in place | "A value that cannot designate a location inside the DAGs directory must never be redirected to a different location" + client-error sentence | maybe — a fix that treats `..` as an opaque name and stores `...yaml` inside the dir returns 200 and moves the file; but that is a redirect and skips the mandated client error, so it is not compliant. Resolved: no | medium |
| …::TestSecSyncEntryOutsideDAGsDirectory | mixed pull (one encoded traversal entry, one nested legit entry) → **200**, no outside file, nested entry written | "No identifier, name, path, or entry — however it is spelled or encoded, and whichever party supplies it — …" | **yes** — a fix that refuses the pull with a client error and writes nothing (the literal reading of "must be refused with a client error and must leave the filesystem unchanged") fails both the 200 and the nested-file assertion | high |
| functional/task_api_functional_test.go::TestFuncCreateReadUpdateDelete | create dotted name 201 + file; read/update 200; delete 204; file gone | "Create, read, update, rename, delete, and run keep their current success responses for every DAG whose file lives inside the DAGs directory." | no | low |
| …::TestFuncCreateWithDefaultSpec | create with name, no spec → 201; default template readable | "Creating a DAG with a workflow body and creating one without a body both keep working." | no (the sibling security case uses an escaping name, not this one) | low |
| …::TestFuncRenameToDottedName | rename `old-name` → `new.name_2` → 200; target exists; source gone | "DAG names may contain dots. Dots are part of the documented name alphabet and stay legal wherever a DAG name is accepted." | no | low |
| …::TestFuncSyncNestedEntries | clean pull → 200, success true, `sub/normal.yaml` and `memory/MEMORY.md` written under the DAGs dir | "DAG files that already live in subdirectories of the DAGs directory keep working in those subdirectories." + "Everything that works today keeps working exactly as today." | no | low |
| functional/project/{filedag_store_test,core_names_test,gitsync_service_test}.go::all (675 cases, restored byte-identical) | the project's own suites for the affected packages keep passing (e.g. `ValidateDAGName("")` must stay nil; `dagIDToFilePath` keeps its signature/outputs) | "Everything that works today keeps working exactly as today." These files are visible in the solver's repo. | no — a fix that rejects `""` inside the shared name rule or changes `dagIDToFilePath`'s signature fails here, but `go test` on the repo shows it, so it is visible material | low–med |

## 2. Leniency (quality, non-blocking)

| concept (trap) | most plausible WRONG fix | caught? |
|---|---|---|
| T1 read/delete | guard only `GetDAGSpec`, not delete | yes — TestSecDeleteOutsideDAGsDirectory (checks/sf-reads-only.patch) |
| T1 | guard only the reported literal `..%2F` string on read/delete | **not caught** |
| T4 create | keep the documented (spec-present) validation branch only | yes — TestSecCreateOutsideDAGsDirectory (checks/sf-no-create-check.patch) |
| T4 | reject only absolute names (`HasPrefix("/")`) | **not caught** (no relative-traversal create case) |
| T4 | leave `name: ""` unguarded | **not caught** — today `path.Join(baseDir,"")` + extension yields `<dagsdir>.yaml` outside the dir; the reference adds an empty-name 400, no test exercises it |
| T5 rename | sanitize the destination to a safe in-dir fallback and return 200 | yes — TestSecRenameOutsideDAGsDirectory (status + source-still-exists; checks/sf-no-dot-check.patch) |
| T5 | drop dots from the shared name alphabet | yes — TestFuncRenameToDottedName (checks/ff-overbroad.patch) |
| T5 | reject only the exact strings `.` and `..` | **not caught** (no `../x` or absolute rename destination) |
| T6 sync | guard request fields / the reported route only | yes — TestSecSyncEntryOutsideDAGsDirectory (checks/sf-reported-only.patch) |
| T6 | skip only entries whose encoded name contains `%2E%2E` | **not caught** (one encoding, one shape tested) |
| all | refuse every request (or return 5xx as refusal) | yes — ff-refuse-all, sf-crash |
| cross-route | ban every name containing a separator, breaking API reads of DAGs in subdirectories | **not caught** — no test drives the API against a subdirectory DAG (only sync entries are nested) |
| cross-route | guard the HTTP handlers only; the store/agent-context path stays open | **not caught** (all tests are HTTP; notes' scope note confirms the chat path shares the lookup) |

Wrong fixes no test catches: relative-traversal create names; empty create name; relative/absolute rename destinations; literal-encoding-only blocks on read/delete; second-entry-shape gaps on sync; a global separator ban; API-only guards.

## 3. Hints (quality, non-blocking)

| quote | why it is a hint | neutral wording |
|---|---|---|
| "A client requested `/api/v1/dags/..%2F..%2Fnotes/spec` …" | names the exact route and encoding of the reported site | "A request naming a DAG navigated outside the configured directory and returned a workflow file that was never placed there." |
| "…for creating, reading, updating, renaming, deleting, and running them" | variant list of operations | "…for managing and running them" |
| "Create, read, update, rename, delete, and run keep their current success responses …" | variant list pointing at each tested route | "Every operation that succeeds today keeps its current success response for every file that lives inside the DAGs directory." |
| "Creating a DAG with a workflow body and creating one without a body both keep working." | names the T4 stage split; exists only to cover that trap | "Every kind of creation that succeeds today keeps working." |
| "DAG names may contain dots. Dots are part of the documented name alphabet …" | names the T5 trap alphabet | "Every name that is accepted today stays accepted." |
| "DAG files that already live in subdirectories … keep working in those subdirectories." | describes the nested format used by the T6 control | "Every file already stored under the configured directory keeps working where it is." |
| "The value in the example above is an example, not the full set of values or forms that must be refused." | points back at the reported shape | "The requirement below applies to every value and every form it can take." |
| "An attempt made through the HTTP API must be refused …" | names the channel, and the word "HTTP API" is the entry point | "A request that carries such a value either fails with a client error and changes nothing, or completes without performing that write." |
| title "DAG names can reach files outside the DAGs directory" | names the mechanism (names) the fix should use | "Files outside the DAGs directory can be read, changed, or removed." |

## 3a. Required: generalize

1. Title "DAG names can reach files outside the DAGs directory" → "Files outside the DAGs directory can be read, changed, or removed."
2. "A client requested `/api/v1/dags/..%2F..%2Fnotes/spec` and the server returned the contents of a YAML workflow file that was never placed in the configured DAGs directory." → "A request naming a DAG navigated outside the configured directory and returned a workflow file that was never placed there."
3. "the server offers an HTTP API for creating, reading, updating, renaming, deleting, and running them" → "the server offers an interface for managing and running them."
4. "Create, read, update, rename, delete, and run keep their current success responses for every DAG whose file lives inside the DAGs directory." → "Every operation that succeeds today keeps its current success response for every file that lives inside the DAGs directory."
5. "Creating a DAG with a workflow body and creating one without a body both keep working." → "Every kind of creation that succeeds today keeps working."
6. "DAG names may contain dots. Dots are part of the documented name alphabet and stay legal wherever a DAG name is accepted." → "Every name that is accepted today stays accepted."
7. "DAG files that already live in subdirectories of the DAGs directory keep working in those subdirectories." → "Every file already stored under the configured directory keeps working where it is."
8. "The value in the example above is an example, not the full set of values or forms that must be refused." → "The requirement above applies to every value and every form it can take."
9. "An attempt made through the HTTP API must be refused with a client error and must leave the filesystem unchanged." → "A request that carries such a value either fails with a client error and changes nothing, or completes without performing that write."

## 4. Realism (quality, non-blocking)

All four trap sites are real, unmodified pinned-commit code reachable through the real server
(T1 skipped request validation whose OpenAPI pattern is never mounted; T4's separately written
default-template branch; T5's dot-preserving rule; T6's URL-decoding join that ignores the existing
`safeDAGIDToFilePath`). None is planted or contrived. The pre-cloned local git remote in the sync
fixture replays what the service itself does and drives the real `/api/v1/sync/pull` path; no fixture
bypasses a valid guard layer. The only contrivance is the sync test's demand that a mixed
malicious-plus-legitimate pull return 200 with the legitimate entry written — that is a test-design
problem (gate a), not a planted trap.

## Stacking checks

| check | concept | result |
|---|---|---|
| S1 coupled traps | T1 — TestFuncCreateReadUpdateDelete vs "Create, read, update, rename, delete, and run keep their current success responses …" | dotted in-dir name only; no security rule forbids it — consistent |
| S1 | T4 — TestFuncCreateWithDefaultSpec vs "Creating a DAG … without a body both keep working" | legitimate name, legitimate no-spec create; security rule refuses only escaping names — consistent |
| S1 | T5 — TestFuncRenameToDottedName vs "DAG names may contain dots …" | no keep-working clause or fixture says `..` is a legitimate name; the refusal is a shape question (S2) — no literal contradiction |
| S1 | T6 — TestFuncSyncNestedEntries vs the subdirectory clause | nested entries are inside the directory — consistent |
| S2 shape traps | T1 | refused `..%2Fsecret` is outside the stated name alphabet and does not resolve inside — ok |
| S2 | T4 | refused absolute path is outside the alphabet — ok |
| S2 | T5 | refused `..` is a dot-only string, and dots are stated to be in the name alphabet — borderline; medium |
| S2 | T6 | refused decoded `../evil.yaml` escapes; the legitimate `sub/normal.yaml` in the same fixture is still accepted — ok |
| S3 fixtures/harness | all | every server is started with the configured DAGs dir; sync is enabled and configured; all guards reachable through the real routes. T1–T5 via the real handlers (dispatcher or store both pass); T6 through the real pull write path, where no request field exists, so the gitsync layer is the only valid one — no layer bypass |
| S4 independence / masking | all | each per-concept `security_fail` patch fails only its own test (manifest `misses` + notes); all five security tests fail on pinned, so nothing is masked |
| S5 history | T1, T4, T5, T6 | `checks/upstream_first_fix.patch` (fix A alone) violates the literal property: T1 and T6 stay open; A+B still leaves T6 open. The property is correctly wider than upstream. No dependency bump. |
| S6 contracts | all | tests need no guessed field or function; the protected object is named in product terms ("DAG file", "configured DAGs directory"); no authority or fail-open fallback exists |
| S7 decisive tests | all | no `build/stk-dagu-ghsaph8x/trial_summary.md`; `trial_detail_deepseek.json` and `trial_detail_mimo.json` show all six runs at 0.8, i.e. one security test decided every run, and the build artifacts do not record which. Re-check that test first and set NEEDS_HUMAN_REVIEW |

## Verdict

**NOT READY.** One gate-a mechanism: `TestSecSyncEntryOutsideDAGsDirectory` demands `200` (and the
legitimate nested file written) from a pull that carries an escaping entry, while the instruction says
such an attempt "must be refused with a client error and must leave the filesystem unchanged". A
correct fix that refuses the whole pull with a 4xx and writes nothing — the literal reading, and the
one the "value must never be redirected" clause supports — fails that test twice. The test accepts
only the per-entry-skip reading. No other test needs a specific refusal form, and every other route
passes at either a dispatcher or a store-layer guard (pass-alt proves the store layer).

Required to remove the unfairness (keep the instruction, change the test per the 2026-10-20 rule):
in `TestSecSyncEntryOutsideDAGsDirectory`, drop `require.Equal(http.StatusOK, code)`; accept either
(a) a client error with no file created anywhere, or (b) 200 with no file outside the directory and
the nested entry written; assert in both branches that the outside file does not exist. `TestFuncSyncNestedEntries`
already pins the clean 200 success path, and `sf-no-sync-guard` still fails because pinned writes the
outside file, so discrimination is preserved. Pair it with the step-3a rewording of the refusal
sentence, which states both permitted forms.

Required: generalize — see the nine items in section 3a.

Quality to tighten: add a relative-traversal create name and an empty create name; add `../escaped`
and an absolute rename destination; add a second encoding on read/delete and a second entry shape
(absolute, nested-encoded) on sync; add one functional test that reads/updates a DAG living in a
subdirectory through the API (today a global separator ban passes while violating that contract);
run the api package's own tests as well (only `^TestSec`/`^TestFunc` run there).

Human review: confirm the sync refusal form (whole-request 4xx versus per-entry skip, and whether the
test should accept both) and whether "dots stay legal" was meant to cover the dot-only name `..`; and
identify which single security test produced 0.8 in all six trial runs (not recorded in build/).

GATE_A: NOT_READY
NEEDS_HUMAN_REVIEW: YES
