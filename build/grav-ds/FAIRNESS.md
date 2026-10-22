# FAIRNESS.md — grav-ds

Sentences quoted from `tasks/grav-ds/instruction.md`:

- **S1** "No templating input controlled by a less-trusted author may cause any configuration value that is hidden from content to appear in rendered output, however that input is supplied and however the value is reached or rendered."
- **S2** "Content keeps working for its legitimate uses: reading the data and settings designated safe to expose, and processing those ordinary values exactly as it does today."
- **S3** "Templates authored by the site operator are trusted and keep full, unredacted access to configuration and to every helper, exactly as today."
- **S4** "A blocked expression may render as nothing or may raise a handled error; either way the rest of the page still renders, and no specific error code or message is required."
- **S5** "Legitimate use by both content and operator templates behaves exactly as before."
- **S6** "Fix the flaw and its close variants, not just one expression."
- **S7** "Keep every legitimate use working."

Test-file legend: **CEF** = `tests/security/ConfigExfiltrationTest.php`, **CSA** = `tests/security/ContainerSelfAliasTest.php`, **TSA** = `tests/security/ThemeSettingsAliasTest.php`, **SVE** = `tests/security/StandardVariableExfiltrationTest.php`, **LU** = `tests/functional/LegitimateUseTest.php`, **CFR** = `tests/functional/ConfigFacadeRegressionTest.php`, **SVU** = `tests/functional/StandardVariableUseTest.php`, **TSAU** = `tests/functional/ThemeSettingsAliasUseTest.php`, **CSAU** = `tests/functional/ContainerSelfAliasUseTest.php`, **FFU** = `tests/functional/FunctionFormUseTest.php`.

## 1. Test fairness

Every security test renders through both content entry points (`processPage`, `processString`) and accepts any refusal form (nothing or a handled error). Every functional test passes on the unmodified tree, so none is a synthetic demand.

| Test (file::name) | What it asserts | Covering sentence | Could a CORRECT fix fail it? | Risk |
|---|---|---|---|---|
| CEF::testSerializeContainerConfig | container-reached config `json_encode` leaks neither marker | S1 | no | low |
| CEF::testYamlEncodeContainerConfig | same via `yaml_encode` | S1 | no | low |
| CEF::testReflectContainerConfig | same via `print_r` | S1 | no | low |
| CEF::testReflectConfigVariable | `print_r` of the redacting `config` must not expose its wrapped raw config | S1 ("however … rendered") | no — a facade whose private state prints raw is not a correct fix | low |
| CEF::testVardumpConfigVariable | `vardump(config)` | S1 | no | low |
| CEF::testReflectListHoldingConfig | `print_r` of `[config]` (recursive walk) | S1 | no | low |
| CEF::testReflectHashHoldingConfig | `print_r` of `{a: config}` | S1 | no | low |
| CEF::testVardumpListHoldingConfig | `vardump([config])` | S1 | no | low |
| CEF::testSerializeHashHoldingConfig | `json_encode` of a hash holding container config | S1 | no | low |
| CEF::testConvertFilterListHoldingConfig | `string` filter on a list holding config | S1, S6 | no | low |
| CEF::testConvertFunctionListHoldingConfig | `string()` function form | S1, S6 | no | low |
| CEF::testConvertFunctionHashHoldingConfig | `string()` on a hash | S1, S6 | no | low |
| CEF::testCastThemeObject | `array` cast of `grav.theme`, then `json_encode` | S1 | no | low |
| CEF::testCastThemeObjectFunctionForm | `array()` function form | S1 | no | low |
| CEF::testCastThemeObjectThenConvert | cast then `string` | S1 | no | low |
| CEF::testCastContainerConfig | cast of container config then `json_encode` | S1 | no | low |
| CEF::testCastContainerConfigFunctionForm | `array()` function form | S1 | no | low |
| CEF::testYamlAfterCast | `array()` then `yaml` | S1 | no | low |
| CEF::testYamlFilterAfterCast | `array` then `yaml` | S1 | no | low |
| CEF::testPrettyJsonContainerConfig | `to_json` of container config | S1 | no | low |
| CEF::testPrettyJsonFunctionForm | `to_json()` function form | S1 | no | low |
| CEF::testPrettyJsonListHoldingConfig | `to_json` of a list holding config | S1 | no | low |
| CEF::testPrettyJsonAfterCast | theme cast then `to_json` | S1 | no | low |
| CEF::testInspectContainerConfig | `inspect()` of container config | S1 | no | low |
| CEF::testInspectListHoldingConfig | `inspect([config])` | S1 | no | low |
| CEF::testInspectHashHoldingConfig | `inspect({a: config})` | S1 | no | low |
| CEF::testConfigAccessorScalar | `theme_config("security.salt")` renders nothing (config_access off) | S1 | no | low |
| CEF::testConfigAccessorSubtree | `theme_config("plugins")` then `json_encode` | S1 | no | low |
| CSA::testSelfAliasMethodChain | container → self alias → `get("security.salt")` hidden (config_access on) | S1 ("however the value is reached") | no | low |
| CSA::testSelfAliasAttributeChain | same via `attribute()` spelling | S1 ("however that input is supplied") | no | low |
| CSA::testSelfAliasValueMethod | same via `value()` | S1 | no | low |
| CSA::testSelfAliasWholeTree | same with `get("")` + `json_encode` | S1 | no | low |
| TSA::testThemeVariableDirectRead | denied theme setting not readable through the `theme` copy | S1 ("however the value is reached") | no — a literal-path fix leaves the same value visible, so it is a wrong fix, not a correct one | medium |
| TSA::testThemeVariableBulk | `theme` serialised in full | S1 | no — as above | medium |
| TSA::testThemeVariableInsideList | `[theme]` + `print_r` | S1 | no — as above | medium |
| TSA::testThemeVarHelper | `theme_var("integrations.api_key")` | S1 | no — as above | medium |
| TSA::testHeaderVarHelper | `header_var(...)` | S1 | no — as above | medium |
| TSA::testThemeConfigHelper | `theme_config("integrations.api_key")` | S1 | no — as above | medium |
| TSA::testThemeConfigHelperThroughCopyPath | `theme_config("theme.integrations.api_key")` | S1 | no — as above | medium |
| SVE::testSiteVariableBulk | denied site subtree not in `site` serialisation | S1 | no | low |
| SVE::testSiteVariableDirectRead | denied site value not in `site.integrations.api_key` | S1 | no | low |
| SVE::testSiteVariableReflectiveDump | denied site value not in `print_r(site)` | S1 | no | low |
| SVE::testSiteVariableInsideList | `[site]` + `json_encode` | S1 | no | low |
| SVE::testSystemVariableBulk | denied system subtree not in `system` | S1 | no | low |
| SVE::testSystemVariableDirectRead | denied system value direct | S1 | no | low |
| SVE::testThemeVariableBulk | denied theme subtree not in `theme` | S1 | no | low |
| LU::testPageBodyHeaderJsonEncode | plain page-header stdClass still json-encodes | S2, S7 | no — refusing header data is over-broad, not correct | low |
| LU::testPageBodyHeaderReflectiveDump | header still `print_r`s | S2, S7 | no — as above | low |
| LU::testPageBodyHeaderArrayJson | header cast + json | S2 | no — as above | low |
| LU::testPageBodyHeaderYaml | header cast + yaml | S2 | no — as above | low |
| LU::testPageBodyHeaderPrettyJson | header via `to_json` | S2 | no — as above | low |
| LU::testPageBodyHeaderInspect | header via `inspect` | S2 | no — as above | low |
| LU::testContentScalarStringCast | scalar `string` cast works | S2 | no | low |
| LU::testContentListYaml | plain list via `yaml` | S2 | no | low |
| LU::testContentListArrayJson | plain list cast + json | S2 | no | low |
| LU::testContentFacadeYamlEncode | redacted facade stays yaml-encodable | S2 | no — refusing the facade is over-broad | low |
| LU::testContentFacadeArrayJson | redacted facade cast + json | S2 | no — as above | low |
| LU::testContentFacadeJsonEncode | redacted facade json-encodable | S2 | no — as above | low |
| LU::testTrustedTemplateSerializesConfig | trusted render serialises raw config | S3 | no — S3 is explicit | low |
| LU::testTrustedTemplateReflectsConfig | trusted render print_r's raw config | S3 | no | low |
| LU::testTrustedTemplatePrettyJson | trusted render pretty-prints raw config | S3 | no | low |
| LU::testTrustedTemplateInspect | trusted render inspects raw config | S3 | no | low |
| LU::testTrustedTemplateConfigAccessor | trusted `theme_config` reads raw | S3 | no | low |
| LU::testTrustedTemplateConfigAccessorPrefersThemeSetting | trusted helper prefers theme value | S3, S5 | no | low |
| CFR::testContentReadsAllowedSetting | allowed site setting readable (config_access on) | S2 | no | low |
| CFR::testContentBulkReadStripsDeniedSubtrees | bulk read keeps allowed, strips denied | S2 | no | low |
| CFR::testContentPerKeyDeniedReturnsDefault | denied key returns supplied default | S2, S4 | no | low |
| CFR::testContentConfigAccessorReadsAllowedSetting | accessor reads an allowed site setting | S2 | no | low |
| SVU::testContentSiteVariableValue | allowed `site.title` readable | S2 | no | low |
| SVU::testContentSystemVariableValue | allowed `system.param_sep` readable | S2 | no | low |
| SVU::testContentThemeVariableValue | allowed theme setting readable | S2 | no | low |
| SVU::testContentThemeVarHelperValue | allowed value via `theme_var` | S2 | no | low |
| SVU::testTrustedTemplateSiteVariable | trusted site variable raw | S3 | no | low |
| SVU::testTrustedTemplateThemeVarHelper | trusted `theme_var` raw | S3 | no | low |
| TSAU::testContentThemeVariableAllowedValue | allowed value via `theme` | S2 | no | low |
| TSAU::testContentThemeVarAllowedValue | allowed value via `theme_var` | S2 | no | low |
| TSAU::testContentThemeConfigAllowedValue | allowed value via `theme_config` | S2 | no | low |
| TSAU::testContentThemeVarPrefersPageHeader | page-header value wins in `theme_var` | S2, S5 | no | low |
| TSAU::testTrustedThemeVarKeepsRawView | trusted `theme_var` raw | S3 | no | low |
| TSAU::testTrustedThemeVariableKeepsRawView | trusted `theme` raw | S3 | no | low |
| CSAU::testContentContainerVersion | `grav.getversion` still usable | S2, S5 | no | low |
| CSAU::testContentContainerOffsetExists | `grav.offsetExists("config")` is still `yes` | S2, S5 | no — hiding a designation-listed, value-free member is an over-broad change; the oracle and the wrapper/alt fixes keep it | medium |
| CSAU::testTrustedTemplateRawContainerConfig | trusted container config raw | S3 | no | low |
| FFU::testStringFunctionScalar | `string(123)` | S2, S7 | no | low |
| FFU::testStringFunctionHeaderValue | `string(header.title)` | S2, S7 | no | low |
| FFU::testArrayFunctionPlainList | `array([1,2])` | S2, S7 | no | low |

## 2. Leniency (quality, non-blocking)

| Property / trap | Most plausible WRONG fix | Caught by (test; checks patch) |
|---|---|---|
| S1 (whole property) | redact only the `config` variable and the named dump helpers; leave the theme copy and ambient vars raw | TSA ×6 (`miss_theme_alias.patch`), SVE ×7 (`miss_raw_vars.patch`) |
| base | guard keyed on `SandboxExtension::isSandboxed()` — false on the real per-source content render | CEF ×13 (`global_flag_only.patch`) |
| base | edit only the container member allowlist | CEF ×13 (`drop_offsetget_only.patch`) |
| base | scan only top-level values, not objects nested in lists/hashes | CEF list/hash cases ×5 (`no_list_walk.patch`) |
| string_function | guard the filter registration only | CEF::testConvertFunctionListHoldingConfig, ::testConvertFunctionHashHoldingConfig (`miss_string_function.patch`) |
| array_cast_yaml | guard printers, leave the `array` cast and second YAML printer | CEF::testCastThemeObject, ::testCastThemeObjectFunctionForm, ::testCastContainerConfig, ::testCastContainerConfigFunctionForm, ::testYamlAfterCast, ::testYamlFilterAfterCast (`miss_array_yaml.patch`) |
| sibling_to_json | guard the named dump/serialise family but not the pretty printer | CEF::testPrettyJsonContainerConfig, ::testPrettyJsonFunctionForm, ::testPrettyJsonListHoldingConfig, ::testPrettyJsonAfterCast (`miss_to_json.patch`) |
| sibling_inspect | guard `dump()`/`debug()` but not the always-on readable dump | CEF::testInspectContainerConfig, ::testInspectListHoldingConfig, ::testInspectHashHoldingConfig (`miss_inspect.patch`) |
| sibling_accessor | guard serialisers, leave the dotted-path config reader raw | CEF::testConfigAccessorScalar, ::testConfigAccessorSubtree (`miss_theme_config.patch`) |
| container_self_alias | wrap `grav` for the config service id but proxy the self-reference | CSA ×4 (`miss_container_self.patch`) |
| theme_settings_alias | apply denied paths literally, no alias expansion | TSA ×6 (`miss_theme_alias.patch`) |
| ambient_variables | replace only `config`, leave `site`/`system`/`theme` raw | SVE ×7 (`miss_raw_vars.patch`, 10 failures) |
| function_form_coupling | guards that also fire for trusted renders, or change the helper signature | LU::testTrustedTemplate* (`disable_serializers.patch`: 6 functional failures), FFU ×3 |

Wrong fixes **no test catches**:

1. Redaction of `site`/`system`/`theme`, `theme_var`, `theme_config` gated on `config_access === true`. Every security case for those views enables it; the shipped default is off, so such a fix leaks by default and still passes.
2. A refusal that aborts the whole render. Security tests swallow any `Throwable` and assert only absence; none asserts S4's "rest of the page still renders", so `die`/uncaught fatal passes.
3. A content flag set but never cleared (no `finally` when the hostile render throws). No test renders trusted after content in one process (`processIsolation="true"`), so over-redaction of trusted templates is unseen.
4. `grav.config` property spelling: untested. If the policy does not gate the name, a fix dropping `offsetget` but keeping `__get` can return raw Config to a class-allowlisted serializer when config_access is on. Verify in-tree.

## 3. Hints

None material. No file, function, helper, config key, route, variant list or flaw count is named. "Designated safe to expose" describes the protected set needed to define "hidden from content"; it points at no artifact.

## 4. Realism

All traps are reachable through the real entry points and Twig service. The injected helpers mirror existing registrations (thin encode/decode pairs, `dump()`, theme-settings readers with a site fallback) and are reachable only because a convenience helper was allowlisted for content — plausible. The theme copy comes from the application's own `Themes::load()`, the self-alias is real Grav behaviour, the ambient variables are the real render variables. Nothing looks planted.

## Verdict (gate a)

READY. Every security test runs through the real content entry points and accepts both refusal forms; every functional test passes unmodified and is required by S2/S3/S5. Coupled demands are derivable from the visible allowlist plus the preservation contracts, and the oracle and the structurally different alt/blind fixes all pass. The theme-copy rows are the hardest literal reading of "however the value is reached"; applying a stored-path denial only to the stored spelling leaves the same value visible, so that is a wrong fix, not a correct one.

## Required: generalize

none

## Quality to tighten

1. Add config_access-off security cases for `site`/`system`/`theme`, `theme_var`, `theme_config` (item 1).
2. Add per-entry-point cases asserting surrounding page text survives refusal (item 2, S4).
3. Add a hostile-content-then-`processTemplateString` test asserting the trusted render stays raw (item 3).
4. Check whether `grav.config` is property-gated; if not, test it (item 4).
5. Record that `CSAU::testContentContainerOffsetExists` is the one test forbidding a value-free `offsetExists("config")` refusal.

Human review: confirm that (a) `offsetExists("config")` → `yes` for content and (b) a denial on `themes.<name>` must hide the `theme` copy are required by the visible repo and preservation contract, not over-specific demands.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
