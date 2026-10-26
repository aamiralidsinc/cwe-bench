# freemarker-ds — build notes

Start: 2026-10-24T04:57:28Z (pipeline start). Finish: 2026-10-24T06:33Z.
Repo: apache/freemarker. Pinned: 3e0d0c02f72c429f3c101fe46891df14a9b0539d. Published fix: 83953d9a9fa5a7c1fce3e39ff57182c19a34b5eb.
Pattern A, track injected.

## Levers (one line each)

- T1 (published site, HOW-type): the raw `Locale.toString()` is appended to the already-normalized
  template name (`TemplateCache.java:924`), so language/country/variant parts carrying `/` and `..`
  escape the template root; a check on the name never sees them. Reason to dismiss: the report leads
  to name normalization, which already rejects `..`.
- T2 (producer/defaults route, HOW-type): the same locale arrives through the configuration default
  (`Configuration.getTemplate(name)` → `getLocale()`) and through a template-level locale setting
  picked up by inclusion (`Environment.java:3098`); a fix at the convenience API passes the reported
  example and misses these. Reason to dismiss: a configuration default / template setting reads as
  local configuration, not caller input.
- T3 (published far site, lower-level public API): `ClassTemplateLoader.java:142` tests the stored
  base package path for `"/"`, which never holds for the ClassLoader constructor, so a URL-shaped name
  reaches `ClassLoader.getResource`. Reason to dismiss: it is a URL-scheme check, not a `..` check,
  and looks configuration-dependent.
- S1 (injected sibling): `LocaleDirectoryTemplateLookupStrategy` turns the locale into directories;
  locale parts with `/` + `..` escape. Reason to dismiss: opt-in strategy, not the default path the
  report exercises.
- S2 (injected sibling): the default strategy uses the custom lookup condition as an optional
  override directory (`TemplateLookupStrategy.java:114`); a condition value escapes, and inclusion
  inherits the condition. Reason to dismiss: not locale at all; a different lookup parameter.

## Candidate routes found and why the picks won

Full candidate list (search of the cache/lookup layer plus the servlet module):

1. `TemplateCache` localized infix (published fix site) — picked T1: the report's landing point and the
   strongest HOW-type shape (value appended after the check), with three distinct locale parts.
2. `ClassTemplateLoader` root/scheme guard (published fix far site) — picked T3: covered by the
   published fix, lower-level public API, different file, clear dismissal.
3. Configuration-default locale (`getTemplate(name)` → `getLocale()`) — picked as part of T2: real,
   unmodified upstream, not described by the report.
4. Environment locale + inherited custom lookup condition in `getTemplateForInclusion` — picked as
   part of T2: real upstream second arrival path.
5. `StringUtil.deduceLocale` producer (locale setting string → `new Locale(...)`) — not a standalone
   lever: fixing the producer alone leaves the direct-API route open, and the check never calls it.
   Folded into T2's template-setting delivery route.
6. `WebappTemplateLoader` (javax-servlet) has no containment check at the pinned commit — rejected:
   the locale route into it is closed transitively by the T1 fix, so it is not an independent lever;
   and it would add a second module plus a container-dependent `getRealPath`/`getResource` stub.
7. `WebappTemplateLoader` loader-level localized fallback — rejected: loaders never receive the
   locale, so making it locale-aware would be unnatural code.
8. `FreemarkerServlet` per-request locale path (servlet module) — rejected: needs a servlet
   container/mocks and is container-dependent; too heavy for an offline verifier.
9. Injected alternate locale-directory strategy — picked S1: a built-in convention the class docs
   themselves describe as legitimate (`foo.ftl` → `en/foo.ftl`), opt-in, separate file.
10. Injected condition-directory handling in the default strategy — picked S2: different input,
    default-reachable, keep-old-fallback so no existing project test changes.
11. Injected per-locale template extension convention (`foo.ftl.en`) — rejected: same concept as S1
    (a second locale→path builder), no new reason to dismiss.
12. Injected legacy localized lookup for old `incompatibleImprovements` — rejected: duplicates the
    infix builder for a BC branch and collides with the project tests that assert old-II behaviour;
    a variant rather than a new concept.
13. `_CoreLocaleUtils.getLessSpecificLocale` change in the published fix — out of scope: number/date
    format alias lookup, not template paths.
14. `TemplateNameFormat` normalization (the report's landing point) — not a lever: it already rejects
    `..`; the flaw is the post-normalization append.

## What I verified

- The flaw reproduces at the pinned commit through the real public API on JDK 17 with the project's
  own `ClassTemplateLoader`: `Configuration.getTemplate("t.ftl", new Locale("en","US","sub/../../secret"))`
  renders a marker file from outside the template root (temporary class-path root; harmless markers).
- All five levers reproduce on the injected pinned tree (see manifest `verified.entry_point`).
- Project tests for the area (29 tests across the five cache/lookup classes) pass on the injected
  pinned tree and on the oracle.
- Test-image emulation (same compiler, parser and jars as the image) gives, per tree:
  baseline security 0/10, functional 54/54; oracle 10/10 and 54/54; every `security_fail` patch leaves
  all functional passing and fails at least one security test; the `functional_fail` patch fails 17
  functional tests; both `pass` patches score full.
- The injection and all check patches apply with `patch -p1` to the pinned tree.

## What I could not verify

- Whether the URL-scheme route is reachable with a stock JDK 17 `URLClassLoader`: it is not (the
  class loader refuses to back out of a class-path entry and does not interpret scheme strings). The
  T3 security test therefore uses a class loader that resolves URL-shaped resource names — the exact
  class of loader the product's own guard comment names. The product-code change is still exercised
  end to end (pinned resolves the outside file, fixed refuses).
- `present_in_latest` for the two injected siblings: they are authoring additions, so "no"; for the
  real routes, current upstream (HEAD of the clone, later than the published fix) contains the fix,
  so "no". No read-only look at a released 2.3.36 artifact was made.
- The project's Gradle build was not used (it needs JDK 8/9/16 toolchains and network). The verifier
  compiles the same sources with `javac --release 8` from a pre-generated JavaCC parser and the same
  compile-only jars; the one source file that needs `com.sun.*` XPath internals
  (`SunInternalXalanXPathSupport.java`) is excluded, which does not affect the cache/lookup area.
- The advisory text itself was never available (the GHSA page returns 404); the mechanism is derived
  from the published fix and confirmed behaviourally.

## Notes / scope

- Outside this advisory's scope, one line: `freemarker-javax-servlet` (`WebappTemplateLoader`) had no
  containment check at the pinned commit; it was not built on (closed transitively by the T1 fix).
- The published fix commit is mostly a formatting/refactor commit; only the locale-infix and
  class-loader-root hunks are behavioural, and `solution/fix.patch` contains only behavioural changes.

## Gate results (2026-10-24)

- static: PASSED (only the downstream `blind` patch and FAIRNESS.md are absent, as expected).
- nop: PASSED — security 0/10, functional 54/54.
- oracle: PASSED — 3 runs, reward 1.0, identical results.
- patches: PASSED — all five `security_fail` patches fail exactly their lever's tests with every
  functional test passing; `ff-drop-localized-lookup.patch` is `functional_fail`; `pass-hardening`
  and `pass-alt` both score 1.0.
- The shared `/var/run/docker.sock` daemon had a wedged `/version` endpoint (load average >100);
  the gate stages were run against a task-private dockerd
  (`~/.tb-graders/cwe/work/freemarker-ds/priv-docker/docker.sock`, bridge 10.240/16, pool 10.248/16),
  following the recorded workaround. No images or containers of other sessions were touched.
