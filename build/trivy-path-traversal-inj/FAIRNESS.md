# FAIRNESS — trivy-path-traversal-inj

Reviewer: pre-trial fairness/leniency review (BUILDER.md 3h). Static review only; nothing was run.
Inputs read: instruction.md, tests/{security,functional,support,pristine}, tests/test.sh, tests/score.py,
solution/fix.patch, environment/inject.patch, manifest.json, notes.md, checks/*.patch.

Path facts used below: plugin root = `$XDG_DATA_HOME/.trivy/plugins`; `filepath.Join(root, "../x")` =
`$XDG_DATA_HOME/.trivy/x`; `filepath.Join(root, "../../x")` = `$XDG_DATA_HOME/x`.

## 1. Per-test fairness

| Test | Asserts | Instruction basis | Can a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/sec_traversal_test.go::TestSec_InstallEscapingName | Install from a local source whose metadata name is `../escaped_plugin` does not create `.trivy/escaped_plugin`; error ignored | "Installing a plugin whose packaged metadata declares a hostile name … writes the plugin's files above the plugins directory"; invariant 1 | No. Refusing, sanitizing (`Base`) and root-confined (`os.Root`) fixes all pass. Exception: a fix that changes `NewManager`'s signature (as upstream does) will not compile (see note A) | low (medium per note A) |
| security/…::TestSec_UninstallEscapingName | `Uninstall("../secret")` leaves `.trivy/secret/keep.txt` in place | "…can also cause files or directories outside the plugins directory to be removed"; invariant 1 ("a value supplied on the command line", "removes") | No. Refusing or treating it as a no-op both pass | low |
| security/…::TestSec_RefreshStoredName | Installed dir `legit` whose stored name is `../../escaped_refresh`; `Refresh("legit")` writes no `.refreshed` into `$HOME/escaped_refresh` | invariant 1 ("metadata already stored on disk from an earlier install", "re-reads") | No. Taking the dir from where it was read (oracle), rejecting the stored name (hardening.patch), or a Refresh-local check all pass | low |
| security/…::TestSec_PrefetchEscapingName | `Prefetch("../../escaped_prefetch")` creates no `$HOME/escaped_prefetch.cache` | invariant 1 ("an entry in the plugin index", "prepares a cache") | No | low |
| functional/func_legit_test.go::TestFunc_InstallLocal | Install from a local path installs `root/goodplugin/{test.sh,plugin.yaml}` | "Installing a plugin from a local filesystem path … must still work" | No. It catches only the over-broad check on the source argument (func_overbroad) | low |
| functional/…::TestFunc_InstallNested | Single wrapping dir is unwrapped; `root/nestedplugin/test.sh` exists | "A source archive that wraps the plugin inside a single top-level directory is unwrapped" | No | low |
| functional/…::TestFunc_UninstallExisting | `Uninstall("goodun")` returns no error and removes the dir | standard expected behaviour; "Keep every legitimate use working" | No | low |
| functional/…::TestFunc_UninstallMissing | `Uninstall("ghost")` returns nil | "Removing a plugin that is not installed succeeds as a no-op" | No | low |
| functional/…::TestFunc_RefreshNormal | `Refresh("goodref")` returns nil and writes `root/goodref/.refreshed` | "Reading or re-reading an already-installed, normally named plugin … works exactly as today, with its files staying inside its own subdirectory" | No (dir name equals stored name) | low |
| functional/…::TestFunc_PrefetchNormal | `Prefetch("goodpf")` creates `root/goodpf.cache/index.json` | "…or preparing a cache for one, works exactly as today" | No | low |
| pristine manager_test.go::TestManager_Run | project's own Run behaviour | "Keep every legitimate use working" | No (the solver can run it) | low |
| pristine::TestManager_Uninstall | removes the dir; for a missing plugin, exact log line `ERROR [plugin] No such plugin` | no-op sentence + existing behaviour | Maybe. A fix that adds or rewords a log line on the not-found path fails the exact-string compare. The solver can see and run this test | low |
| pristine::TestManager_Information | exact info output; exact "could not find a plugin called 'unknown'…" error | existing behaviour | Maybe. Same exact-string caveat, but the test is visible | low |
| pristine::TestManager_LoadAll | `LoadAll` over `testdata` returns exactly one plugin with exported fields equal | existing behaviour | No (the unexported `dir` is not compared) | low |

Note A (medium): every hidden test calls `plugin.NewManager()` with no arguments, plus `Manager.Refresh/Prefetch/Install/Uninstall` with today's signatures. The upstream-style fix (open an `os.Root`, return an error from the constructor) is reasonable, but a fix that changes these signatures fails to compile. Compile failure zeroes both groups. The instruction never says the Go API must stay stable. The project's visible tests would also break, which partly mitigates this, but a solver may update those tests on the assumption that the API can change. Fix: add a sentence (see §5).

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| base_install | guard only the CLI/source argument, not the metadata name | yes: TestSec_InstallEscapingName (sec_miss_base.patch) |
| far_uninstall | guard install only ("CLI arg is trusted") | yes: TestSec_UninstallEscapingName (sec_miss_uninstall.patch) |
| sibling_reload | guard the `load` argument but keep the dir derived from the stored name | yes: TestSec_RefreshStoredName (sec_miss_refresh.patch) |
| sibling_prefetch | skip Prefetch ("curated index, cache only") | yes: TestSec_PrefetchEscapingName (sec_miss_prefetch.patch) |
| over-broad refusal | apply `IsLocal` to the install source | yes: TestFunc_InstallLocal (func_overbroad.patch) |
| CLI-argument route into `load` (Refresh / Information / Run with `../..`) | oracle minus the `load()` guard: `plugin.dir = dir` alone makes the dir come from `filepath.Join(root, name)`, so `Refresh("../../outside")`, where `outside/plugin.yaml` exists, writes `outside/.refreshed`. Information/Run would read outside the root | **NO.** No test calls `Refresh`, `Information` or `Run` with an escaping argument, and no check patch removes the `load()` guard. The oracle's `load()` guard is therefore untested |
| bare `..` | `if filepath.Base(name) != name` or `strings.Contains(name, "../")` as the guard. Both let `..` through: `Uninstall("..")` does `RemoveAll($HOME/.trivy)`, and an install with metadata name `..` clears and writes `.trivy` | **NO.** Every test name has the form `../x` or `../../x` |
| prefix sibling | `strings.HasPrefix(filepath.Join(root,name), root)` without a separator, so `../plugins_evil` escapes | **NO.** No test name shares the root's prefix (`withinRoot` in alt_fix is correct; nothing distinguishes the buggy form) |
| "read" invariant | leave read-only paths unguarded | **NO.** No test asserts on reads (see the `load` row) |
| "no partial result" | validate after `plugin.install` has already written `dst` | partly: for install, the out-of-root dir check catches it. No test checks partial state inside the root |
| `.` as name | `Uninstall(".")` RemoveAll's the plugin root itself (the oracle allows this: `IsLocal(".")` is true) | not tested; arguably not "outside" the plugins directory, so acceptable |

Wrong fixes that no test catches: no guard on the `load` argument; `Base`-equality or `../`-substring guards (`..`); `HasPrefix` without a separator; unguarded reads.

## 3. Hints in instruction.md

1. "a few maintenance operations that re-read an already-installed plugin, or prepare a cache for one listed in the plugin index" paraphrases the two injected methods (Refresh, Prefetch). → "and a few maintenance operations."
2. "This holds for every source a name can come from — a plugin's packaged metadata, a value supplied on the command line, metadata already stored on disk from an earlier install, or an entry in the plugin index" is a variant list that maps 1:1 onto the four traps. It also cancels the reason-to-dismiss for sibling_reload and sibling_prefetch. → "This holds for every place a plugin name can come from, including data Trivy itself wrote earlier." (Optionally stop at "come from"; standard expert knowledge says persisted copies of untrusted input stay untrusted.)
3. "and for every plugin management operation, whether it installs, removes, reads, re-reads or prepares a cache for a plugin" lists the operations and so the sinks. → "and for every plugin management operation."
4. "Depending on which management command is used, the same class of crafted name can also cause files or directories outside the plugins directory to be removed or newly created." points at uninstall (removed) and prefetch (created). → delete, or "Other management commands are affected in similar ways."
5. "When a plugin is installed, that metadata is also stored on disk alongside the plugin." points at the stored-name trap. It is acceptable as background only if items 2–3 are made neutral. Keep it and accept the residual hint, or drop it.
6. "Reading or re-reading … or preparing a cache for one" (Keep working) repeats the Refresh/Prefetch paraphrase. → "Every other plugin management operation on a normally named plugin works exactly as today."

No leak terms, file names, function names, CVE IDs or flaw count found.

## 4. Realism

- base_install and far_uninstall: real upstream code, reachable via `trivy plugin install/uninstall`. OK.
- sibling_reload: the stored-name → dir derivation is real upstream code. The injected `Refresh` is wired to `trivy plugin refresh`, so it is reachable. However, it writes a `.refreshed` marker that, despite its comment, nothing (including `list`) ever reads. It looks planted. **Medium.** Make some real consumer use the marker (e.g. `List` shows a refreshed time), or have Refresh do real work (re-read and re-save the metadata).
- sibling_prefetch: the comment says it is "for a plugin listed in the index so that a subsequent install can reuse the downloaded assets". But the code never consults the index (`tryIndex` is not called), and install never reads `*.cache`. The name is a raw CLI argument, so the manifest's "index-entry name / curated index is trusted" story is not true of the code. **Medium.** Either resolve the name through the index (and have install reuse the cache), or relabel the source as the CLI argument in the manifest and the instruction.

## 5. Verdict: NOT READY

Required changes:
1. **Tests (tighten):**
   - (a) Add `TestSec_RefreshEscapingArg`: create `$HOME/outside/plugin.yaml`, call `Refresh("../../outside")`, assert there is no `$HOME/outside/.refreshed`. Add `checks/sec_miss_load.patch` (oracle minus the `load()` guard, expect security_fail).
   - (b) Add a bare-`..` case: `Uninstall("..")` with a sentinel in `.trivy/`, plus an install with metadata name `..` or `../plugins_evil`. Add check patches for a `Base`-equality guard and a separator-less `HasPrefix` guard (expect security_fail).
2. **Instruction (neutralize):** apply the §3 rewrites for items 1, 2, 3, 4 and 6.
3. **Instruction (add):** "Keep the package's exported Go API (constructors and method signatures) unchanged."
4. **Realism:** make Prefetch actually index-backed and Refresh's marker actually consumed, or drop the "index entry" framing from the manifest and the instruction.

Re-run the patch gate after these changes.
