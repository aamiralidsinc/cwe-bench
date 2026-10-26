# trivy-path-traversal-inj — build notes

- Start: 2026-10-18T04:45Z
- End: (see end_utc.txt)

## Task
GHSA-8RC5-4FR6-64PW / CVE-2026-63328, aquasecurity/trivy, CWE-22. Pattern A+B,
track INJECTED. Pinned 246ee3ca (verified parent of fix d4213d77). Mechanism:
a plugin name (from packaged metadata, stored metadata, a CLI argument, or an
index entry) is joined onto the plugin root ~/.trivy/plugins to form a directory
that is written / deleted / created; at the pinned commit nothing confines it.

## Seam
Pure Go unit tests driving the real pkg/plugin.Manager methods with XDG_DATA_HOME
at a temp dir (the project's own test style). Offline; no services; no network.
Toolchain: go1.26.3 + GOEXPERIMENT=jsonv2 (the repo imports encoding/json/v2;
go1.27 renamed json.SkipFunc so the full project will not build under it).

## Levers (each verified: fails on pinned+inject, passes on oracle)
- base_install (A, published): packaged-metadata name '../x' → install writes/clears outside root. Dismiss: none (obvious). sec_miss_base.
- far_uninstall (A, published): CLI name '../secret' → RemoveAll outside root. Dismiss: CLI arg is the user's own input, trusted. sec_miss_uninstall.
- sibling_reload (injected): stored-metadata name '../../x' → maintenance op writes outside root via the stored-name→dir derivation. Dismiss: metadata was written by Trivy itself, trusted; a fix on the install argument misses the reload path. sec_miss_refresh.
- sibling_prefetch (injected): index-entry name '../../x' → cache dir created outside root. Dismiss: curated index is trusted; read-only cache reservation. sec_miss_prefetch.

## Oracle
Signature-stable confinement (filepath.IsLocal at the install destination, the
uninstall argument, the load argument, and the prefetch name; installed
directory derived from the directory read rather than the stored name). Keeps
NewManager()'s signature so the project's own pkg/plugin tests compile/pass
unchanged. fix.patch = inject→oracle (manager.go only).

## Verified
- nop (pinned+inject): 4 security FAIL, 13 functional PASS.
- oracle: all pass.
- every check patch behaves as declared (sec_miss_{base,uninstall,refresh,prefetch} each fails exactly its lever; func_overbroad fails install functional; hardening + alt_fix pass).
- project pkg/plugin suite builds+passes on pinned+inject and oracle.
- pinned does NOT contain the advisory regression tests (added only by the fix commit).
- instruction.md: no leak terms, no CVE/GHSA/sha, no fix filenames; 512 words.

## Could not verify / notes
- present_in_latest for the base/far sites assumed from the fix diff (os.Root confinement); not re-pulled from current main.
- Platform.Bin exec-path route (plugin.go:69) investigated and left out (different field/sink; plugin author already runs code) — matches the screener's recommendation; registered.
- The upstream fix changes the NewManager signature and uses os.Root; the oracle intentionally diverges (signature-stable) for test compatibility. Not byte-identical to upstream, but closes every lever and keeps functional green.
- Install suite with the httptest git server is run at build time, not in the grader, to keep the functional group deterministic.

## Gate result (2026-10-18)
- static: clean except the blind pass-patch and FAIRNESS.md (left for downstream, as instructed).
- nop: PASSED (4 security fail, functional pass).
- oracle: PASSED (3x identical, reward 1.0).
- patches: PASSED — sec_miss_{base,uninstall,refresh,prefetch} each 0.75 (3/4 security, one lever open); func_overbroad 0.0 (functional_fail); hardening + alt_fix 1.0.
- Gotcha fixed mid-build: the functional -run filter had a trailing `$` that stopped the task's own TestFunc_* coupled tests from running (only project TestManager_* ran). Dropped the anchor; func_overbroad then correctly fails. Re-ran nop/oracle/patches after the fix — all pass.
