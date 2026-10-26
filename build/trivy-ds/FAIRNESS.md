# trivy-ds — pre-trial fairness and leniency review

Legend: **P1** = L11 "No plugin name — however Trivy obtained it, and whichever plugin management operation uses it — may cause a file or directory outside the plugin directory to be created, written, removed, read or executed." **P2** = L12 "A name that leaves the plugin directory only after its path is interpreted ... is covered as well." **P3** = L13 "A name that would escape must be refused or treated as absent: the operation may return an error or do nothing, and in either case it must leave everything outside the plugin directory untouched." **P4** = L14 "A name that stays inside the plugin directory keeps working exactly as it does today, including the files each management operation writes inside it and the programs it starts from there."

The security tests discard the returned error, so every refusal form P3 allows (error, nil, nothing) is accepted. Functional tests require nil errors only for the legitimate operations they name.

## 1. Test fairness (one row per graded test)

| Test (file::name) | What it asserts | Covering sentence | Correct fix could fail it? | Risk |
|---|---|---|---|---|
| security/ds_security_test.go::TestSec_InstallEscapingName | Packaged name `../escaped_plugin`: outside sentinel kept; no `plugin.yaml` written outside | P1 (created/written; "however Trivy obtained it") + P3 | no — reject before the destination is cleared; error or no-op both pass | low |
| security/ds_security_test.go::TestSec_InstallCleanEscape | `missing/../../escaped_clean` creates no directory outside | P1 | no — lexical or resolved containment both refuse | low |
| security/ds_security_test.go::TestSec_InstallPrefixSibling | `../plugins_evil` creates no directory next to the plugin directory | P1 ("outside") | no — a separator-aware containment check refuses | low |
| security/ds_security_test.go::TestSec_InstallSymlinkEscape | `link/sub` through an existing link: outside sentinel kept; no metadata written through it | P2 (first clause already covers it; the link parenthetical is redundant) | no — a lexical-only fix fails, but P2 requires resolution | low |
| security/ds_security_test.go::TestSec_UninstallEscapingName | `Uninstall("../secret")` leaves the outside directory | P1 ("removed", "whichever ... operation") + P3 | no — error ignored | low |
| security/ds_security_test.go::TestSec_InformationEscapingName | `Information("../../outside")` prints none of the outside metadata | P1 ("read") | no — error or silent absence both pass | low |
| security/ds_security_test.go::TestSec_UninstallParentName | `Uninstall("..")` leaves the directory above the plugin directory | P1 + P3 | no — `IsLocal`/containment refuses | low |
| security/ds_security_test.go::TestSec_StoredNameExecution | `Start("legit")` with stored name `../../escaped_exec` executes nothing outside | P1 ("however Trivy obtained it", "executed") | no — refusing the stored name or using the directory read from both pass | low |
| security/ds_security_test.go::TestSec_RepairStoredName | `Repair()` with stored name `../../escaped_repair` creates/writes nothing outside | P1 ("whichever ... operation", "created, written"); Repair is visible in the repo | no — resolve, skip, or rewrite-in-place all pass | low |
| security/ds_security_test.go::TestSec_IndexEntryName | Update's cache for index name `../../escaped_index` creates no directory outside | P1 ("however Trivy obtained it", "created") | no — skip or error both pass; the index copy is still stored | low |
| functional/ds_functional_test.go::TestFunc_InstallLocal | Local-path source installs `test.sh` + `plugin.yaml` under the plugin directory | P4 + L18 (path/URL sources keep working) | no | low |
| functional/ds_functional_test.go::TestFunc_InstallNested | Single top-level wrapper is unwrapped | L19 | no | low |
| functional/ds_functional_test.go::TestFunc_UninstallExisting | Installed plugin is removed | P4 | no | low |
| functional/ds_functional_test.go::TestFunc_UninstallMissing | Missing plugin: nil | L20 | no | low |
| functional/ds_functional_test.go::TestFunc_StartNormal | In-directory program starts | P4 ("programs it starts from there") | no | low |
| functional/ds_functional_test.go::TestFunc_RepairNormal | Repair rewrites `usage` to `summary` in place | P4 ("files each management operation writes inside it") + repo-visible Repair | no | low |
| functional/ds_functional_test.go::TestFunc_RepairMissingRoot | Repair returns nil with no plugin root | P4 + repo-visible Repair | no | low |
| functional/ds_functional_test.go::TestFunc_UpdateCachesIndex | `index.yaml` and the per-entry `index.json` are stored inside | L21 + P4 | no | low |
| functional/ds_functional_test.go::TestFunc_UpdateUnparsableIndex | Unparsable index: nil, and `index.yaml` keeps the bytes | L21 | no | low |
| pristine/manager_test.go::TestManager_Uninstall | Found plugin removed; missing logs "No such plugin" and returns nil | P4 + visible project test (current behavior) | no | low |
| pristine/manager_test.go::TestManager_Information | Exact render for a valid plugin; not-found error for "unknown" | P4 + visible project test | no | low |
| pristine/manager_test.go::TestManager_LoadAll | testdata plugin loads; missing root errors "failed to read" | P4 + visible project test | no | low |
| pristine/manager_test.go::TestManager_Run | Bare `Plugin.Run` starts the testdata bin; error cases unchanged | P4 ("programs it starts") + visible project test | no — a fix that drops the Name fallback would regress visible behavior | low |

Not graded: pristine `TestManager_Install`, `TestManager_Upgrade`, `TestManager_Update`, `TestManager_Search` are outside the `-run` alternation (build-time project suite only).

## 2. Leniency (quality, non-blocking)

| Trap | Most plausible wrong fix | Caught? |
|---|---|---|
| base_install | Validate the install *source* (`IsLocal(src)`) or only the CLI, leaving the metadata-name join at the destination | Yes: the three install tests still see the outside effect; `func_overbroad.patch` shows the source guard also breaks `TestFunc_InstallLocal`/`Nested`; `sec_miss_install.patch` |
| symlink_install | `filepath.IsLocal` only, no link resolution | Yes: `TestSec_InstallSymlinkEscape`; `sec_miss_symlink.patch` (0.9) |
| far_cli_name | Guard writes only; leave Uninstall/Information on the plain join | Yes: the three uninstall/info tests; `sec_miss_cli.patch` (0.7) |
| stored_name_dir | Guard `load(name)` but keep `plugin.dir` derived from the stored name | Yes: `TestSec_StoredNameExecution` + `TestSec_RepairStoredName`; `sec_miss_stored_dir.patch` (0.8) |
| sibling_index_cache | Fix everything in manager.go, leave Update's cache loop | Yes: `TestSec_IndexEntryName`; `sec_miss_index.patch` (0.9) |
| catalogue | `refuse_all`, `reads_only`, `prefix_guard`, `weak_guard` | Yes: functional tests for refuse_all; security tests for the rest (`prefix_guard` caught by prefix + link, `weak_guard` by bare `..` + link) |

**Wrong fixes no test catches:**
1. Symlink resolution only at install; `IsLocal`-only at Uninstall/load/Repair/Update. Only Install is driven through a link.
2. `EvalSymlinks(dst)` on the full path with `fs.ErrNotExist` allowed: the test's link points at an existing `sub`, so a fix that misses `link/new` passes.
3. Guarding the *argument* of Information only: `Start`/`Run` with an escaping CLI name (`Start("../../escaped_exec")`) is never driven; only the stored-name route is.
4. Basename-sanitizing instead of refusing: `../escaped_plugin` installed as `<root>/escaped_plugin` passes every assertion, though P3 requires refusal/absence.
5. The injected `cachedRepository` read (`<root>/<name>.index/index.json`) is unguarded in the oracle and untested — a literal P1 "read" left open.
6. Blanket rejection of any name containing `/` passes every functional test (none uses an in-directory multi-component name), contrary to P4.

## 3. Hints (quality)

| Quote | Why | Neutral wording |
|---|---|---|
| L7 "declares the name `../escaped_plugin` creates a plugin directory above the plugin directory and deletes whatever was already stored there" | Exact test input plus the delete effect | "declares a relative name that climbs out of the plugin directory creates a directory outside it and deletes what was stored there" |
| L12 "including one that goes through a link that already exists inside the plugin directory" | Names the symlink shape; exists only to cover one trap | "A name is judged by where it actually resolves, not by how its text looks." |
| L3 "Trivy reads that metadata when it installs the plugin and stores a copy next to the installed files" | Points at the install stage / metadata-copy write | "Trivy reads that metadata and keeps a copy of it with the plugin's files." |
| L18 "it normally contains `/` and is not itself a plugin name" | Tells the solver not to validate the source (fix approach) | "Install sources, which are filesystem paths or URLs, keep being accepted." |

## 3a. Required: generalize

- L12: remove "including one that goes through a link that already exists inside the plugin directory". It exists only to cover the symlink trap. State the property once over the outcome: "A name that leaves the plugin directory only after its path is interpreted is covered as well." (TestSec_InstallSymlinkEscape stays covered by this clause.)

## 4. Realism

- base_install, symlink_install and far_cli_name are real pinned/published-fix code; no scope flag applies.
- stored_name_dir: `loadMetadata` and the exec join are real. The injected `Repair` is plausible migration code reachable via `trivy plugin repair`; writing to `p.Name` rather than the directory it read from is the same idiom as the real bug, though slightly convenient. Not planted-looking.
- sibling_index_cache: Update already writes into the plugin root, so a per-plugin cache is plausible; the `file://` index mirror is a faithful stand-in for a remote feed. Its read-back `cachedRepository` is a second real-looking sink.

## 5. Verdict

Every graded test is covered by P1–P4 read literally, including the stored-name, repair and index routes ("however Trivy obtained it", "whichever plugin management operation"). Security tests ignore the error and assert only outside effects, so error and no-op refusal, and a guard at any valid layer before the sink, all pass; no test demands one error class or status. Functional tests restate explicit legitimate use or behavior visible in the repo (the injected Repair/cache are in the repo), and the API-shape bullet keeps the harness compiling (`alt_fix.patch` with `os.Root` also scores 1.0). No correct-fix-fails mechanism found: READY. The uncaught wrong fixes above are gate-b only. A CLI-dispatcher-only guard would fail, but it is not a correct fix: P1 governs the operations and the exported `Manager` methods are those operations.

**Required: generalize:** L12 — drop "including one that goes through a link that already exists inside the plugin directory"; keep the general clause "A name that leaves the plugin directory only after its path is interpreted is covered as well", which still covers TestSec_InstallSymlinkEscape.

**Quality to tighten:** (1) add symlink-name tests on Uninstall/Information/Repair/Update; (2) add a `link/new` (non-existent child) install case; (3) add `Start`/`Run` with an escaping argument; (4) assert an escaping install leaves nothing inside the root either, rejecting basename sanitizing; (5) `resolve` the injected `cachedRepository` read and test it; (6) add a functional in-directory multi-component install (`sub/plugin`); (7) apply the four hint rewordings in §3 and the §3a generalization.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
