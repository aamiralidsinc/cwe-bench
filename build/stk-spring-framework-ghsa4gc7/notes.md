# stk-spring-framework-ghsa4gc7 — build notes

## Window
- Start: 2026-10-26T12:14:46Z (from `start_utc.txt`)
- End: (filled at hand-off)

## Pinned / fixes
- Pinned (vulnerable): `spring-projects/spring-framework` @ `0cf7f7bd890504061883c48e382dc23e0c5d4df0` (5.3.19-SNAPSHOT).
- A (GHSA-g5mm-vmx4-3rg7 / CVE-2022-22968): `a7cf19cec5ebd270f97a194d749e2d5701ad2ab7`; its parent is the pinned commit,
  so the published patch applies to the checkout. Fix A makes the *disallowed* patterns case-insensitive by
  lowercasing patterns at set time and the compared name at match time (bare `toLowerCase()`).
- B (GHSA-4gc7-5j7h-4qph / CVE-2024-38820): `23656aebc6c7d0f9faff1080981eb4d55eff296c`; replaces the bare
  `toLowerCase()` with `toLowerCase(Locale.ROOT)` at both sites. The DataBinder hunks apply on top of A.

## Levers (one line each)
- **T1/T2 — case variants (advisory route).** The screen compares the canonical field byte-exactly against the
  excluded patterns, while the bean resolver accepts a first-character case variant at every segment
  (`CachedIntrospectionResults` uncapitalize/capitalize fallback), so `Name`, `spouse.Age` and a wildcard-protected
  `address.City` all reach the property. Fix: fold both sides (patterns and name) at compare time.
- **T3 — locale-dependent fold (how-type, MiMo).** The natural fix uses the default-locale `toLowerCase()`, which
  under a Turkish regional setting maps `I` to `ı` and drops the match in both directions. Fix: locale-independent
  fold. This is exactly the later published fix B.
- **T4 — map-key text is data (coupled value, MiMo).** Bracketed map keys are selector data converted as such by
  the accessor; a fold/normalisation over the whole field changes which entries a legitimate submission writes.
  Functional guard for the index lever.
- **T5 — lexical vs resolved index (unprotected route, DeepSeek).** The screen compares `items[00]`/`items[+0]`
  lexically while the accessor parses the selector with `Integer.parseInt`, so both reach element 0 although the
  excluded name spells `items[0]`. No published fix touches it; it is still unhandled in current main.

## What was verified (local, offline Gradle against a warmed cache)
- Pinned: 8/8 security tests fail; 8/8 functional tests pass; the project's own `DataBinderTests` (79) and
  `DataBinderFieldAccessTests` (6) pass.
- Reference fix (`solution/fix.patch`): 8/8 security, 8/8 functional, 85/85 project.
- Variant matrix (12 runs, each parsed from the JUnit XML): `base` 8/8 security fail + all functional pass;
  `oracle` 1.0; `upstream_first_fix` (A alone) → T3 and T5 open, functional pass; `upstream_fix` (A+B) → T5 open,
  functional pass; `miss_case` → case + locale open, functional pass; `miss_locale` → T3 open only; `miss_index`
  → T5 open only; `functional_fail` (whole-name numeric normalisation) → map-key functional test fails;
  `refuse_all` and `crash_as_refusal` → functional fail; `pass_hardening` and `pass_alt` → all pass.
- Control task (`stk-spring-framework-ghsa4gc7-control`): same report, only the direct-route security test and the
  A-only reference.
- `present_in_latest`: current `main` (read 2026-10-26) uses `PatternMatchUtils.simpleMatchIgnoreCase`; the
  index-spelling route is still unhandled, and map-key text is still folded with the rest of the name.

## What could not be verified / unknowns
- The reader record file named in `stacking.reader_record` is not present in this checkout; the design follows the
  record embedded in the build prompt (reproduced verbatim there).
- The 2024 fix was written against a much later 5.3.x tree; only its two DataBinder hunks were taken, and they
  apply with fuzz. The repository's own `DataBinderTests` at the pinned commit are unchanged by the reference fix,
  which was verified by running them.
- Whether a blind engineer finds T5 without a hint is the main fairness question (see report).

## Environment plumbing
- The pinned `settings.gradle` applies Gradle Enterprise build-scan plugins that were published only on
  `repo.spring.io`, which now returns 401. `environment/build-infra.py` (copied into both images) removes those two
  plugin lines and the build-scan block. No product or test source is touched. Without it the tree cannot build.
- Both images warm the Gradle wrapper, plugins, dependency graph and test runtime classpath; the verifier keeps a
  pristine copy of the module test sources at `/opt/project-tests.tgz`.
