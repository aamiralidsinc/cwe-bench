# FAIRNESS — grav-info-exposure-inj

Pre-trial fairness/leniency review (BUILDER.md 3h). Static only: nothing was run, and no upstream
code was consulted. I read instruction.md, all of tests/ (bootstrap, SandboxTestCase, 3 test
classes, score.py, test.sh), solution/fix.patch, environment/inject.patch, manifest.json, notes.md,
checks/*.patch and gate_report.json. The grav source tree is not present locally. Claims about Twig and Grav
internals therefore rest on notes.md and on the patches.

Test seam: every test renders through `SandboxTestCase::sandboxEnv()`. That is a fresh Twig env with
`new SandboxExtension(Security::buildTwigSandboxPolicy(), true)`, which means a **globally** sandboxed
env, with test-supplied vars (`config` = SandboxConfig facade, `grav` = raw container). The "trusted"
env is the same env with `false`. `Twig::processPage()/processString()` are never executed.

## 1. Per-test table

| Test | Asserts | Instruction basis | Correct fix could fail? | Risk |
|---|---|---|---|---|
| security::testSerializeContainerConfig | `grav.offsetGet("config")\|json_encode` shows no marker | Prop. 1: "regardless of … helper … reached indirectly through another object" | **maybe**: a fix that marks sandboxed renders in `Twig::processPage/processString` (render-scope flag) and does not also read the env's global sandbox flag never activates here (S1) | high |
| …::testReflectContainerConfig | same via `\|print_r` | Prop. 1 | maybe (S1) | high |
| …::testYamlContainerConfig | same via `\|yaml_encode` | Prop. 1 | maybe (S1) | high |
| …::testReflectConfigVariable | `config\|print_r` does not expose the facade's private Config | Prop. 1: "reached indirectly through another object that carries it" | maybe (S1) | high |
| …::testExportConfigVariable | `config\|export` same | Prop. 1: "output-formatting" | maybe (S1) | high |
| …::testConfigAccessorScalar | `theme_config("security.salt")` shows no marker | Prop. 1: "accessor"; §System: security settings are hidden | maybe (S1). Removing it from the content allowlist passes regardless | medium |
| …::testConfigAccessorSubtree | `theme_config("plugins")\|json_encode` shows no marker | Prop. 1: "pulled out in bulk" | maybe (S1) | medium |
| …::testSerializeArrayHoldingConfig | `[grav.offsetGet("config")]\|string` shows no marker | Prop. 1: "nested inside a surrounding value such as a list" | maybe (S1) | high |
| functional::testSandboxedHeaderJsonEncode | `header\|json_encode` contains Hello and World | Prop. 2: "serializing … ordinary values" | no | low |
| …::testSandboxedHeaderReflectiveDump | `header\|print_r` (stdClass) contains Hello and World | Prop. 2: "displaying those ordinary values" | no. Banning print_r in content is ruled out by Prop. 2 | low |
| …::testSandboxedHeaderExport | `header\|export` contains Hello | Prop. 2 | no | low |
| …::testSandboxedScalarExport | `"snippet"\|export` contains snippet | Prop. 2 | no | low |
| …::testSandboxedScalarStringCast | exactly `123/Hello`, rendered **without** the try/catch | Preservation: "exactly as before" | no | low |
| …::testTrustedTemplateSerializesConfig | trusted: `grav.offsetGet("config")\|json_encode` contains the plugin marker | Prop. 3: "full, unredacted access" | no | low |
| …::testTrustedTemplateExportsConfig | trusted: `config\|export`, where `config` is the **facade**, contains the plugin marker | Prop. 3 | **yes**: a fix that hardens the facade itself fails this test. Example: the facade holds a pre-filtered snapshot instead of the live Config, or is otherwise made reflection-safe. That fix is correct and arguably the cleanest way to close the facade-reflection route. The test requires the facade to *keep* leaking under reflection. In the real app, trusted templates get the raw Config as `config` (see the comment in fix.patch/Twig.php), not the facade, so this scenario does not occur in production (S2) | **high** |
| …::testTrustedTemplateConfigAccessor | trusted: `theme_config("security.salt")` returns the marker | Prop. 3 | no. Deleting `theme_config` entirely would fail, but Prop. 3 forbids that | low |
| ConfigFacadeRegressionTest::testFacadeReadsAllowedSubtree | config_access on: `config.get("site.title")` | Preservation: "settings designated as exposable" | no | low |
| …::testFacadeStripsDeniedSubtreeOnBulkRead | `config.toArray()\|json_encode` keeps the title, has no markers | Preservation + Prop. 1 | no. Relies on the shipped `config_denied_paths` | low |
| …::testFacadePerKeyDeniedReturnsDefault | denied key returns `BLOCKED` | Preservation | no | low |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| base: container accessor | Remove `offsetget/__get` from the Grav allowlist only | Yes: testReflectConfigVariable and testExportConfigVariable still leak through the facade |
| base: "core json_encode override looks out of scope" | Guard print_r/yaml_encode/string/export, fix theme_config, remove offsetget, **leave json_encode unguarded** | **No.** Every json_encode security test obtains its object through `offsetGet` (closed by the allowlist edit) or through theme_config (fixed separately). No check patch isolates this case. The trap is not enforced |
| base: list nesting | Guard top-level values only, with no array walk | **No.** testSerializeArrayHoldingConfig is also closed by the allowlist edit |
| base: facade reflection | Guard print_r only | Yes: testExportConfigVariable (miss_export.patch) |
| sibling_export | Guard only the dump family named in the code | Yes: testExportConfigVariable (miss_export.patch, miss_siblings.patch) |
| sibling_accessor | Leave theme_config alone | Yes: testConfigAccessor* (miss_theme_config.patch, miss_siblings.patch) |
| sibling_accessor | Redact with `config_denied_paths` even when config_access is off | No. Low impact, because the markers are in denied paths anyway |
| refuse_all / adjacent_api | Apply the guards unconditionally, including in trusted renders | Yes: testTrustedTemplate* (disable_feature.patch) |

Wrong fixes that no test catches:
1. **Skipping the json_encode override** (above).
2. **Filter form only.** The `print_r()` and `vardump()` *function* registrations stay unguarded. No test calls `{{ print_r(config) }}` or `{{ vardump(config) }}`. Add tests if those functions are in `allowed_functions`.
3. **Subscript spelling.** notes.md says `grav['config']` reaches the Config at pinned. If Twig's ArrayAccess path skips `checkMethodAllowed('offsetget')`, then the allowlist edit alone does not close `grav['config']|json_encode` / `|print_r`, and no test exercises it. Verify on pinned+injected. If it leaks, add the test; it would also enforce item 1.
4. **Class denylist.** A guard that refuses only `Config`/`SandboxConfig` leaves other objects that carry config unprotected, e.g. `grav.theme|print_r`, since `theme` is allow-listed and a Theme/Plugin holds a protected `$config`. The instruction explicitly covers "another object that carries it". Verify the leak, then add the test.
5. **Real-path no-op.** A fix keyed only on the env's global flag, like the oracle, passes every test while staying a no-op in the shipped render path (S1).

Check patches:
- **blind.patch is invalid.** It has no `export` or `theme_config` lines, so it was made against the non-injected tree. Its getFilters/getFunctions hunks will not apply to the injected tree. Even if forced, it leaves both siblings open. gate_report.json shows no stages run. Regenerate it on the injected image and gate it.
- **alt_fix.patch is not a real alternative.** It is the oracle minus the theme_config guard, with theme_config de-allowlisted instead. It does not show that a structurally different fix, such as redaction (the blind agent's own approach) or a render-scope flag, passes.

## 3. Hints in instruction.md

| Quote | Problem | Neutral wording |
|---|---|---|
| "regardless of which expression, helper, accessor, value-cast or output-formatting is used to reach it" | Maps one-to-one onto the tests: accessor = theme_config, value-cast = `\|string`, output-formatting = export/print_r | "regardless of which template construct is used to reach it" |
| "pulled out in bulk, or reached indirectly through another object that carries it" | Describes the container route and the facade-private-state route | "whether read singly, in bulk, or by any indirect route" |
| "nested inside a surrounding value such as a list" | Names the exact shape of testSerializeArrayHoldingConfig | Drop "such as a list" |
| "serialize that data for a snippet" (Magnitudes) | "snippet" echoes the injected export docstring ("copy-pasteable config snippets") | "or render that data in another format" |

No file, function or class names, no flaw count and no leak_terms appear. Property 2's "formatting, serializing or displaying" is needed for the fairness of the functional tests. Keep it.

## 4. Realism

- **export filter.** Plausible. It is a thin var_export twin of print_r, and allow-listing it next to print_r is believable. OK.
- **theme_config.** **Looks planted.** It is named theme_ but reads the whole *site* config, and Grav already ships `theme_var`. Its docstring example reads plugin config. inject.patch also adds it to the sandbox `allowed_functions`, right next to a facade whose stated job is to hide config from content. That is an odd choice for a maintainer. Rename it so the name matches its behaviour, or make it theme-scoped with a fallback, and justify the allowlist entry.
- **Entry point (S1).** notes.md admits that the real `Twig::processPage/processString` sandboxes through a per-source policy. There, `SandboxExtension::isSandboxed()` with no argument returns false. The oracle's `assertSandboxDumpSafe` and `themeConfigGuarded` test exactly that call, so in production they are no-ops. On the real page path, `config|print_r`, `config|export` and `theme_config("security.salt")` still leak under the oracle. The tests certify a reference fix that does not fix the deployed flaw. They can also fail a correct fix that hooks the real render path.

## 5. Verdict: **NOT READY**

Required changes:
1. **(S1, high)** Make the oracle effective on the real path, e.g. a render-scope flag set in processPage/processString, as blind.patch's SandboxContext does. Add security tests that render through `Twig::processString()` or a GravSourcePolicy env. Keep the global-sandbox tests only if a render-flag-only fix also passes them.
2. **(S2, high)** testTrustedTemplateExportsConfig: give the trusted env the raw Config as `config`, as production does, or assert on `grav.offsetGet("config")|export`. Do not require the facade to stay reflectable.
3. **(high, gate)** Regenerate blind.patch against the injected tree and gate it. Replace alt_fix.patch with a structurally different correct fix.
4. **(medium)** Add tests for `grav['config']|json_encode` and `[grav['config']]|string` (after confirming they leak at pinned), for `print_r(config)`/`vardump(config)` and for `grav.theme|print_r`. Otherwise drop the json_encode and list-walk claims from manifest.traps.base.
5. **(medium)** Apply the §3 rewordings.
6. **(medium)** Fix theme_config realism (§4).
