# grav-mm — build notes

Start UTC: 2026-10-18T19:12:12Z
Design written: 2026-10-18T19:39:47Z (BEFORE build)

## Context

Second task on GHSA-MC5Q-6HPJ-RP7J (getgrav/grav, CWE-200). Pinned commit
734f7f4c (parent of 7efe7057). Pattern A+B, track INJECTED.

**Prior task `grav-info-exposure-inj` on this advisory was REJECTED: both DeepSeek
and MiMo solved 3/3.** Their fixes were broad (per-filter guards, SandboxValue
walks, SandboxGrav/SandboxRender facades, config-derived var filtering). One
observed gap in DeepSeek's winning patch: the `string` filter and `string()`
function were left unguarded (they look like scalar casts). This design leans on
that gap plus more uncovered routes and cast-family siblings.

## Plan — levers

Each lever has a distinct reason a solver would skip it.

### L1 base (Pattern A) — published fix's protected sink
- **Shape:** sandboxed page-content Twig reaches raw config (container accessor
  `offsetget`) and/or reflects the redacting config facade's private wrapped
  Config via PHP-side reflective dumpers / serializers. Far sites the published
  fix protects: the Grav allowlist row in defaults YAML (looks like site-owner
  config, not code); a Twig-core `json_encode` override (looks like vendor
  code); a new policy-class public API used by the guard.
- **Where:** GravExtension.php:147-159,198-199 + system/config/security.yaml:335-336
  + fix.diff:59-62 + GravSecurityPolicy::isClassAllowed.
- **Reason to dismiss:** "the allowlist is configuration, not code" and
  "json_encode belongs to Twig core"; a solver guards only `print_r` in
  GravExtension and stops.
- **Tempting wrong fix:** guards keyed on `SandboxExtension::isSandboxed()`
  (no Source arg) — a no-op on the real processPage/processString path, which
  uses a per-source SourcePolicy. Also: drop only `offsetget` from the allowlist.

### L2 string_fn (Pattern B, uncovered) — `string()` FUNCTION
- **Shape:** `string([obj])` / `string({a: obj})` json_encodes the array, calling
  `Data::jsonSerialize` on any Config inside. The published fix guarded only the
  same-named *filter* registration.
- **Where:** GravExtension.php:213 (function list) → stringFilter:860-876.
- **Reason to dismiss:** the report and fix talk about *filters*; `string()` sits
  in the separate function list and reads as a harmless scalar cast helper.
- **Evidence:** DeepSeek's winning patch on the sibling task left string/string()
  unguarded. Route verified LEAK at pinned via `string([grav.offsetGet('config')])`.

### L3 array_cast (Pattern B, uncovered) — `array` filter AND function
- **Shape:** `array(obj)` calls `toArray()` or a PHP `(array)` cast, outside the
  member gate. Exposes protected/private state (`Plugin::$config`, Theme's
  container, service map), which a printer then outputs. Input shapes: bare
  object, object nested in a list/hash.
- **Where:** GravExtension.php:163 (filter) + :189 (function) + arrayFilter:911-928.
- **Reason to dismiss:** `|array` is a type cast, not a dump/serialize filter,
  and the advisory names only offsetGet + dump.
- **Evidence:** `grav.theme|array|json_encode`, `array(grav.theme)|print_r` LEAK
  at pinned with NO offsetGet needed (Theme's protected `$config`).

### L4 yaml_printer (Pattern B, uncovered) — `yaml` filter
- **Shape:** `array(obj)|yaml` — Yaml::dump prints whatever plain array an earlier
  cast hands it. Second YAML printer next to `yaml_encode`, which the fix guarded.
- **Where:** GravExtension.php:164 + yamlFilter:936-939.
- **Reason to dismiss:** "the Symfony dumper refuses to serialize objects, so on
  its own it cannot leak an object" — true in isolation, false after a cast.
- **Evidence:** `array(grav.offsetGet('config'))|yaml` LEAK at pinned.

### L5 derived_vars (Pattern B, uncovered) — raw `system` / `site` / `theme` vars
- **Shape:** sandboxed render inherits raw config subtrees as template variables;
  only `config` is replaced by the redacting facade. Serializing any of them
  prints unredacted config even with `config_access` off (facade deny-all).
- **Where:** Twig.php:298-300 (twig_vars) + Twig.php:411-412,493-495 (sandbox_vars).
- **Reason to dismiss:** documented standard template variables; the default
  denied paths (`plugins`, `security`, …) are not under them — solvers reason
  about `config_access: true` mode and skip.
- **Coupled:** with `config_access: true` these variables must keep working for
  every path not under `config_denied_paths` (they are not in that list).

### L6 sibling_to_json (injected, serializing) — `to_json` filter
- **Shape:** a pretty-print JSON encoder beside `json_decode` ("Casting values" /
  encode-decode neighbourhood), `json_encode($v, JSON_PRETTY_PRINT)`.
- **Where:** GravExtension.php filter registrations, beside `json_decode` (:143).
- **Reason to dismiss:** formatting/pretty-print helper next to a decoder, not
  part of the named dump/serialize family the advisory discusses.
- **Realism:** the extension already has thin encode/decode pairs and casting
  helpers in both filter and function form.

### L7 sibling_inspect (injected, reflective/toArray) — `inspect` function
- **Shape:** non-debug variant of `dump()`/`debug()`: walks context objects with
  `toArray()` and returns a printable string into the page (dump() is debug-gated
  and pushes to the debugger only).
- **Where:** GravExtension.php function registrations, beside `dump`/`debug`/`vardump`.
- **Reason to dismiss:** a page-display helper, not a debug dump; and it *returns*
  a string rather than dumping, so it does not look like the dump family.
- **Realism:** dump()/debug() already do the per-object toArray walk at
  GravExtension.php:1087-1113; a maintainer adding an always-on readable
  variant would reuse that walk.

## Input shapes / forms the security tests cover
- bare object (raw Config via container accessor, redacting facade, Theme);
- array / hash holding objects (recursive walk);
- stdClass page header (must keep working);
- filter form vs function form (`string`, `array`, `print_r`);
- reflective tier (`print_r`, `vardump`, `inspect`) vs serializing tier
  (`json_encode`, `yaml_encode`, `string`, `to_json`, `yaml`);
- both content entry points: `Twig::processPage` and `Twig::processString`.

## Coupled must-keep (functional tests)
- Trusted operator Twig (`processTemplateString`) serializes/reflection-dumps any
  object, including raw Config — unchanged.
- Sandboxed content: `header|json_encode`, `header|print_r`, `header|array|json_encode`,
  `'x'|string`, `123|string`, `header.title|json_encode`, `[1,2,3]|yaml`,
  `config|yaml_encode` (redacting facade) all keep working.
- `config_access: true`: `system`/`site`/`theme` still readable for every path not
  under `config_denied_paths`; per-key denied reads return the default.
- Project's own suites (TwigSandboxTest, SandboxConfigTest) keep passing.

## Sites / routes the security tests cover
See manifest.traps. One test per site, route, shape and form; every test goes
through the real entry point and asserts "no marker in rendered output"
(boolean str_contains — a leaking render is MBs and OOMs phpunit otherwise).

## Injected siblings (2–4 at the recurring trust decision)
Recurring trust decision: **which template helpers may reflect or serialize PHP
object state past the sandbox member gate inside sandboxed page content?**
Siblings L6 (`to_json`) and L7 (`inspect`) sit at that decision, in code the
published fix never touches, each with its own dismissal reason. 2 siblings.

## Producer off the check's path
`Security::buildTwigSandboxPolicy` + `Twig::buildSandboxConfig` (config loader /
policy producer) decide what the member gate and the redacting facade withhold.
The tests do not call the producer; they render through the Twig service and
seed config first. L5 depends on that producer's deny-all mode being consistent
across `config` and the derived vars.

## Not pursued / out of scope
- `print_r()` *function* form — already blocked at pinned (not in
  `allowed_functions`); no route, no test.
- `dump`/`debug` — debug-gated no-ops in production.
- `grav['config']` / `grav.config` subscript — blocked (property `config` not
  allow-listed on Grav).
- `grav.offsetGet('config').get(x)` — already blocked (config_access off strips
  Config methods from the policy).
- Later advisory GHSA-59qm-58v5-gvc5 closed `|array`/`|yaml` upstream; we still
  build on them here (this is our own copy at the pinned commit).
- `system`/`site`/`theme` under `config_access: true` do not contain the default
  denied paths; L5 is tested in the shipped default (`config_access: false`),
  where the facade is deny-all.

## Fairness notes (self-review)
- Every route above was confirmed to leak through `processString` on the pinned
  tree before it became a lever.
- The instruction words one invariant covering all of them ("no value that page
  settings withhold may appear … regardless of which template construct is used")
  and never names a file, filter, function or route.
- L5 is the fairest-risk lever: "documented standard template variables" is a
  real objection. Mitigation: the invariant is about *withheld* config, and with
  `config_access: false` the facade withholds everything — the derived vars
  contradict that. Coupled tests keep them working wherever they are legitimately
  readable (trusted templates; `config_access: true` non-denied paths).

## Build results

End UTC: 2026-10-18T20:09:03Z

### Plan deviations (with reason)
- **L5 derived_vars DROPPED.** The raw `system`/`site`/`theme` template vars do
  not carry the withheld paths (`plugins`, `security`) — they are config
  subtrees, so no marker appears. Out of the advisory's member-gate protection;
  one line, not built on.
- **L3 + L4 MERGED** into one lever `array_cast_yaml`. Both share a fail mode:
  the only fix point is the cast that produces the leaked plain array; the YAML
  printer cannot tell a leaked array from `[1,2,3]` after the cast. One
  security_fail patch (`miss_array_yaml.patch`) covers both shapes.

### Levers as built (5)
1. **base** (Pattern A) — offsetget allowlist + named printers (json_encode /
   yaml_encode / print_r / vardump), recursive list walk, render-scope flag.
2. **string_function** (Pattern B) — conversion helper's *function* registration
   left unguarded by the published fix (DeepSeek's observed gap).
3. **array_cast_yaml** (Pattern B) — type-cast helper + second YAML printer.
4. **sibling_to_json** (injected) — pretty-print JSON filter/function.
5. **sibling_inspect** (injected) — always-on readable dump function.

### Verified at pinned+injected (leak) and pinned+fixed (no leak)
All 20 security shapes were confirmed to leak through `Twig::processString` on
the injected tree and to be blocked on `repo-sol` (the oracle). The oracle keeps
every must-keep functional shape (header json/print_r/array/yaml/to_json/inspect,
scalar string casts, list yaml/array, facade yaml_encode/array/json_encode, trusted
templates, config_access:true facade regression).

### Could not verify
- `inspect(grav.theme)` / `grav.theme|array|print_r` produce 161 MB / 467 MB
  renders at pinned. They leak, but are omitted from the tests (OOM risk under
  processIsolation). The smaller `grav.theme|array|json_encode` shape (88 KB)
  covers the same Theme/protected-state route.
- Project's own Codeception suites were not run here (offline image is built by
  the gate; see FAIRNESS review for that pass).

### Files
- tasks/grav-mm/ (instruction.md, task.toml, environment/, solution/, tests/)
- build/grav-mm/ (manifest.json, checks/*.patch, notes.md)
- build/audit/uncovered-routes.tsv — 4 rows (2 Pattern B, 2 injected)

### Check-patch results observed (all 10 confirmed)
- miss_string_function: reward 0.92, fails testConvertFunctionListHoldingConfig +
  testConvertFunctionHashHoldingConfig; functional all pass. CONFIRMED.
- miss_array_yaml: reward 0.84, fails testCastContainerConfig +
  testCastContainerConfigFunctionForm + testYamlAfterCast + testYamlFilterAfterCast;
  functional all pass. CONFIRMED.
- miss_to_json: reward 0.96, fails testPrettyJsonAfterCast; functional all pass.
  CONFIRMED.
- miss_inspect: sec fail testInspectListHoldingConfig + testInspectHashHoldingConfig;
  functional all pass. CONFIRMED. (testInspectContainerConfig is blocked by the
  offsetGet close — only the offsetGet-free facade shapes leak.)
- global_flag_only: sec fail 11 tests (all render-flag-dependent routes);
  functional all pass. CONFIRMED.
- no_list_walk: sec fail 5 nested-shape tests (inspect/reflect/vardump list+hash);
  functional all pass. CONFIRMED.
- drop_offsetget_only: sec fail 11 tests (every facade/cast route);
  functional all pass. CONFIRMED.
- disable_serializers: fun fail testTrustedTemplateSerializesConfig +
  testTrustedTemplateReflectsConfig + testTrustedTemplatePrettyJson +
  testTrustedTemplateInspect (guard throws for trusted templates too).
  EXPECT functional_fail. CONFIRMED.
- hardening: all sec + fun pass (depth cap 8 is still a correct fix).
  EXPECT pass. CONFIRMED.
- alt_fix: all sec + fun pass (structurally different fix — class denylist
  instead of allowlist walk — still a correct fix). EXPECT pass. CONFIRMED.
- nop: reward 0.00 (all security fail). oracle x3: reward 1.00 each. CONFIRMED
  (run before the 3 extra nested-shape tests; those fail on vulnerable code and
  pass on the oracle — they only exercise facade shapes already covered).
