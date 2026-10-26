# trivy-ds — build notes

- Start: 2026-10-19T18:12Z (pipeline start; design work began here)
- End: 2026-10-19T18:38Z

## Task
GHSA-8RC5-4FR6-64PW / CVE-2026-63328 / GO-2026-6250, aquasecurity/trivy, CWE-22.
Pinned vulnerable commit 246ee3ca56b666e3c6e6462bf7c0ecd6f059341a (verified
parent of the published fix d4213d7735c74e57f06c02ccb39ebca67abc7959).
Mechanism: a plugin name (from packaged metadata, from metadata stored on disk,
from a plugin-index entry, or from a command-line argument) is joined onto the
plugin directory to form a path that is created, cleared, written, removed,
read or executed. At the pinned commit nothing confines the join.

## Plan (written before the build)
Pattern A with injected siblings; 5 levers, each with a different reason a
solver would dismiss or skip it:

1. `base_install` (A, published): packaged-metadata name `../escaped_plugin`
   (plus `missing/../../escaped_clean`, `../plugins_evil`) forms the install
   destination; the downloader clears it and writes the plugin and its
   metadata there. Dismissal: none — the report's own example.
2. `symlink_install` (A, published input shape): the name is a plain relative
   path `link/sub` whose parent inside the plugin directory is an existing
   symlink out of the directory. Dismissal: "a link inside the user's own
   plugin directory means local tampering, not attacker input", and a
   filepath.IsLocal-style check passes the name.
3. `far_cli_name` (A, published far sites): Uninstall and Information join the
   command-line name onto the plugin directory and remove / read through it.
   Dismissal: the CLI argument is the local user's own input; reads of a named
   plugin are intended.
4. `stored_name_dir` (A, published save/reload + exec, with an injected save
   operation): loadMetadata derives the plugin's directory from the name
   recorded in stored metadata (manager.go:414), so Start executes
   `Platform.Bin` outside the directory (plugin.go:69) and the injected
   Repair rewrites metadata outside it. Dismissal: the stored metadata was
   written by Trivy itself, so its name reads as trusted; a fix on the install
   argument alone misses it.
5. `sibling_index_cache` (injected): Update writes a per-plugin index cache
   using the entry name from the downloaded index; tryIndex reads it back.
   Dismissal: the index is a curated feed and the operation only primes a
   cache; a guard on CLI names does not see a name present only in index data.

Coupled must-keep-working behaviour: install sources are paths/URLs containing
`/` (an over-broad IsLocal on the source breaks it); single-top-level-directory
unwrap; uninstall of a missing plugin returns nil; a normally named plugin
still starts and still has its metadata repaired in place; Update still
succeeds (and still stores the index) when the index cannot be parsed.

## Seam
Pure Go unit tests driving the real pkg/plugin.Manager methods with
XDG_DATA_HOME at a temp directory (the project's own test style) and
WithIndexURL at a file-URL mirror for the index route. Offline; no services,
no network, no GPU/GUI. Toolchain: go1.26.3 + GOEXPERIMENT=jsonv2 (the repo
imports encoding/json/v2; go1.27 renamed json.SkipFunc so the full project
does not build under it).

## Oracle
Signature-stable confinement. New helpers `resolve` (filepath.IsLocal plus a
symlink-resolving containment walk of the existing path prefix) and `withinDir`
in pkg/plugin/manager.go; applied at the install destination, Uninstall, load,
the injected Repair and the injected index-cache loop. loadMetadata records the
directory the metadata was read from instead of the name recorded in it.
NewManager keeps its signature so the project's own pkg/plugin tests compile
and pass unchanged. fix.patch = inject→oracle (manager.go + index.go).
alt_fix.patch is a second correct design using os.Root for containment.

## Verified (locally, on the pinned+injected tree and on the oracle)
- Reproduced every lever on pinned+injected through the public Manager
  methods: install writes/clears outside the plugin directory (relative,
  cleaned and prefix-sibling names), install through a pre-existing link,
  Uninstall removes outside, bare `..` removes the directory above the plugin
  directory, Information reads outside, Start executes outside via a stored
  name, Repair writes outside, Update's index cache creates outside.
- nop shape: 10 security tests FAIL, 9 task functional tests PASS; project
  pkg/plugin suite (including TestManager_Install and TestManager_Upgrade)
  builds and passes.
- oracle: 10 security + 9 functional + the project subset all pass; full
  project pkg/plugin suite passes.
- every checks/*.patch behaves as declared locally:
  sec_miss_install (4 install tests), sec_miss_symlink (link test only),
  sec_miss_cli (uninstall/info/bare-parent), sec_miss_stored_dir (exec +
  repair), sec_miss_index (index only), reads_only (8 write-path tests),
  prefix_guard (prefix + link), weak_guard (link + bare parent): security
  fails, functional pass. func_overbroad and refuse_all: functional fails.
  hardening and alt_fix: everything passes.
- pinned does NOT contain the advisory regression tests (they are added only
  by the fix commit).

## Could not verify / notes
- The two target models were not run (per the build rules).
- present_in_latest for the stored-name route is inferred from the fix diff
  (the fix derives the directory from the directory read), not re-pulled from
  current main.
- Platform.Bin itself (the plugin author's own executable path) is left
  unconfined, matching upstream and the screener's advice: it is a different
  field/sink and the plugin author already controls the program. The stored
  name that supplies the *directory* is confined.
- pkg/vex/repo/manager.go joins a VEX repository name onto a cache directory
  with the same class of flaw; it is outside this advisory's protection and
  is not built on (one line here as required).
- The published fix changes NewManager's signature and uses os.Root; the
  oracle intentionally keeps the signature so the project's own tests compile.
  alt_fix.patch demonstrates the os.Root design scoring 1.0.

## Gate result (2026-10-19)
- static: PASSED apart from the two items left for downstream by design (the
  missing `blind` pass patch and the missing FAIRNESS.md).
- nop: PASSED - 10 security tests all fail on pinned+injected, 22 functional
  cases (task + project subset) all pass.
- oracle: PASSED - 3 runs, reward 1.0, identical results.
- patches: PASSED - all 12 checks behave as declared:
  sec_miss_install 0.6 (4 install tests fail, functional green);
  sec_miss_symlink 0.9 (link test only); sec_miss_cli 0.7 (uninstall/info/
  bare-parent); sec_miss_stored_dir 0.8 (exec + repair);
  sec_miss_index 0.9 (index only); reads_only 0.2 (writes only);
  prefix_guard 0.8 (prefix sibling + link); weak_guard 0.8 (link + bare
  parent); func_overbroad 0.0 and refuse_all 0.0 (functional fail);
  hardening 1.0; alt_fix 1.0.
- One infrastructure retry was needed: the first patches run hit a Docker
  network-churn race ("network ..._default not found") on the shared VM; the
  clean rerun passed. No task change was made for it.
