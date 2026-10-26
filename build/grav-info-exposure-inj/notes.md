# grav-info-exposure-inj — build notes

Start UTC: 2026-10-18T01:58:06Z
End UTC: 2026-10-18T02:31:50Z. Gate stages static(expected blind+FAIRNESS remain), nop, oracle, patches all run; nop/oracle/patches PASSED.

## Levers (one line each)
- base (pattern A): sandboxed page content reaches the raw config via a container accessor and serializes/reflects it, or reflects the redacting config facade's private state; the published fix's protected sink spans a vendor-core serializer override (out-of-scope-looking) and a defaults allowlist entry (config-looking). file: GravExtension.php:147-159,198-199 + security.yaml:335-336.
- sibling_export (injected, reflective): an added `export` filter (var_export) reflects an object's private state; dismiss "value-formatting helper, not the named dump family". GravExtension.php (near print_r filter).
- sibling_accessor (injected, accessor): an added `theme_config()` function reads raw config by dotted path past the facade; dismiss "convenience reader, targeted not bulk". GravExtension.php (near vardump function).

## Verified
- Flaw reproduces through the real seam (sandboxed Twig render via buildTwigSandboxPolicy) on pinned+injected: all 8 security tests leak; 11 functional pass.
- Oracle (solution/fix.patch) closes all 8 and keeps 11 functional green; project's own TwigSandboxTest/SandboxConfigTest/GravExtensionTest pass on pinned+injected and after the oracle.
- All six check patches behave as declared (miss_siblings/miss_export/miss_theme_config = security_fail; disable_feature = functional_fail; hardening + alt_fix = pass).
- No leaked regression tests: the published fix commit adds no tests (only CHANGELOG + 3 source files), so none exist between pinned and fix.

## Could not verify / caveats
- Entry-point model: the real `Twig::processString` uses a per-source SourcePolicy under which `SandboxExtension::isSandboxed()` with no source argument returns false, so the published dump-guard is a no-op there. The faithful, deterministic seam (and the one the project's own security suite uses) is a globally-sandboxed Twig env built from `buildTwigSandboxPolicy()`; the tests use exactly that. The member gate (allowlist removal) IS source-aware and works either way.
- The grav container-accessor direct read `grav['config'].get(x)` is already blocked at pinned by the config_access=off stripping of raw Config methods; the serialize/reflect/accessor routes are the live leaks.
- Pattern-A far "allowlist" site is defense-in-depth in the oracle but is not independently required by the tests: the serializer/reflect guards subsume the container route. Not a fairness issue; recorded here.

## Out of scope (one line)
- A later advisory (GHSA-59qm-58v5-gvc5) closed the |array / |yaml cast routes upstream; not pursued here (raises recall risk and needs a secret-bearing object in scope).

## Fairness revision (2026-10-18, addresses FAIRNESS.md "Required changes")
- S1: tests now render through the real Twig service: Twig::processPage (mocked PageInterface, Twig enabled) AND
  Twig::processString for every security snippet; trusted via Twig::processTemplateString. Headless init in
  SandboxTestCase: tmp/cwetheme theme dir, base_url services, $grav['theme'] = Theme. Global-sandbox env dropped
  (a render-flag-only fix would fail it). Oracle adds Twig::isRenderingContent() (depth counter around both content
  renders); guards use isSandboxed() || isRenderingContent(). checks/global_flag_only.patch (old oracle detection) =
  security_fail (7 tests).
- S2: trusted tests get the raw Config as `config` (processTemplateString), not the facade.
- New security tests (all verified to leak at pinned+injected on the real path): vardump(config) (captured via
  VarDumper::setHandler), ["x", config]|print_r (list walk; no_list_walk.patch), grav.theme|export (object carrying
  config; class_denylist.patch). Not routes at pinned (no tests): grav['config'] subscript, print_r() function form,
  grav.theme|print_r|json_encode. json_encode-override claim dropped from traps.base (no independent route).
- Security asserts are boolean (str_contains): a leaking render is MBs and PHPUnit's process-isolation result
  serialization ran out of memory echoing the haystack.
- theme_config realism: now "active theme setting, falling back to site config" (inject.patch regenerated).
- alt_fix.patch replaced: ContentValue render flag + redaction (no refusal, no policy change). blind.patch removed:
  it was made on the non-injected tree; regenerate on the injected image (saved in scratch old-checks/).
- Local verification (scratch run.sh, tests mounted over grav-inj-task image): pinned 11 sec FAIL / 13 func pass;
  oracle, alt, hardening 24/24; miss_* / global_flag_only / no_list_walk / class_denylist security_fail with func green;
  disable_feature functional_fail.
