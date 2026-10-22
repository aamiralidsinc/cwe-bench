<?php

use CweTests\SandboxTestCase;

/**
 * Editor-authored page content must not be able to read back configuration
 * that is hidden from content. Each test renders a hostile snippet as a page
 * body and as an editor-derived string, and asserts that neither marker secret
 * reaches the output, regardless of how the application refuses (soft-fail,
 * thrown error, or redacted value — all acceptable, no exact form required).
 *
 * On the unfixed code each of these leaks a marker; a correct fix makes all of
 * them safe.
 */
final class ConfigExfiltrationTest extends SandboxTestCase
{
    private function assertNoSecret(string $template, string $context): void
    {
        // Boolean asserts: a leaking render can be megabytes, too large to echo.
        $output = $this->renderContent($template);
        self::assertFalse(str_contains($output, self::SECRET_PLUGIN), $context . ' (plugin secret reached the page)');
        self::assertFalse(str_contains($output, self::SECRET_SECURITY), $context . ' (security secret reached the page)');
    }

    // --- container accessor + serializing helpers ---------------------------

    public function testSerializeContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|json_encode|raw }}', 'serializing a container-reached config must not leak');
    }

    public function testYamlEncodeContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|yaml_encode|raw }}', 'yaml-encoding a container-reached config must not leak');
    }

    // --- container accessor + reflective helpers ----------------------------

    public function testReflectContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|print_r|raw }}', 'reflective dump of a container-reached config must not leak');
    }

    // --- redacting facade reached by reflective helpers ---------------------

    public function testReflectConfigVariable(): void
    {
        $this->assertNoSecret('{{ config|print_r|raw }}', 'reflective dump of the config variable must not expose its hidden state');
    }

    public function testVardumpConfigVariable(): void
    {
        $this->assertNoSecret('{{ vardump(config) }}', 'debug-dumping the config variable must not expose its hidden state');
    }

    // --- objects nested in lists and hashes ---------------------------------

    public function testReflectListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ [config]|print_r|raw }}', 'dumping a list that holds the config variable must not leak');
    }

    public function testReflectHashHoldingConfig(): void
    {
        $this->assertNoSecret('{{ {a: config}|print_r|raw }}', 'dumping a hash that holds the config variable must not leak');
    }

    public function testVardumpListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ vardump([config]) }}', 'debug-dumping a list that holds the config variable must not leak');
    }

    public function testSerializeHashHoldingConfig(): void
    {
        $this->assertNoSecret('{{ {x: grav.offsetGet("config")}|json_encode|raw }}', 'serializing a hash that holds a container-reached config must not leak');
    }

    // --- conversion helper, filter form and function form ------------------

    public function testConvertFilterListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ [grav.offsetGet("config")]|string|raw }}', 'converting a list that holds a container-reached config must not leak');
    }

    public function testConvertFunctionListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ string([grav.offsetGet("config")])|raw }}', 'converting a list that holds a container-reached config must not leak');
    }

    public function testConvertFunctionHashHoldingConfig(): void
    {
        $this->assertNoSecret('{{ string({a: grav.offsetGet("config")})|raw }}', 'converting a hash that holds a container-reached config must not leak');
    }

    // --- type-cast helper exposing object state -----------------------------

    public function testCastThemeObject(): void
    {
        $this->assertNoSecret('{{ grav.theme|array|json_encode|raw }}', 'casting a container-reached object that carries config must not leak');
    }

    public function testCastThemeObjectFunctionForm(): void
    {
        $this->assertNoSecret('{{ array(grav.theme)|json_encode|raw }}', 'casting a container-reached object that carries config must not leak');
    }

    public function testCastThemeObjectThenConvert(): void
    {
        $this->assertNoSecret('{{ grav.theme|array|string|raw }}', 'converting a cast of an object that carries config must not leak');
    }

    public function testCastContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|array|json_encode|raw }}', 'casting a container-reached config must not leak');
    }

    public function testCastContainerConfigFunctionForm(): void
    {
        $this->assertNoSecret('{{ array(grav.offsetGet("config"))|json_encode|raw }}', 'casting a container-reached config must not leak');
    }

    // --- second YAML printer after a cast -----------------------------------

    public function testYamlAfterCast(): void
    {
        $this->assertNoSecret('{{ array(grav.offsetGet("config"))|yaml|raw }}', 'yaml-printing a cast of a container-reached config must not leak');
    }

    public function testYamlFilterAfterCast(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|array|yaml|raw }}', 'yaml-printing a cast of a container-reached config must not leak');
    }

    // --- pretty-JSON helper (sibling) ---------------------------------------

    public function testPrettyJsonContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|to_json|raw }}', 'pretty-printing a container-reached config must not leak');
    }

    public function testPrettyJsonFunctionForm(): void
    {
        $this->assertNoSecret('{{ to_json(grav.offsetGet("config"))|raw }}', 'pretty-printing a container-reached config must not leak');
    }

    public function testPrettyJsonListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ to_json([grav.offsetGet("config")])|raw }}', 'pretty-printing a list that holds a container-reached config must not leak');
    }

    public function testPrettyJsonAfterCast(): void
    {
        $this->assertNoSecret('{{ grav.theme|array|to_json|raw }}', 'pretty-printing a cast of an object that carries config must not leak');
    }

    // --- readable-dump helper (sibling) -------------------------------------

    public function testInspectContainerConfig(): void
    {
        $this->assertNoSecret('{{ inspect(grav.offsetGet("config"))|raw }}', 'inspecting a container-reached config must not leak');
    }

    public function testInspectListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ inspect([config])|raw }}', 'inspecting a list that holds the config variable must not leak');
    }

    public function testInspectHashHoldingConfig(): void
    {
        $this->assertNoSecret('{{ inspect({a: config})|raw }}', 'inspecting a hash that holds the config variable must not leak');
    }

    // --- targeted config accessor (sibling) ---------------------------------

    public function testConfigAccessorScalar(): void
    {
        $this->assertNoSecret('{{ theme_config("security.salt") }}', 'a targeted configuration accessor must not read a hidden value');
    }

    public function testConfigAccessorSubtree(): void
    {
        $this->assertNoSecret('{{ theme_config("plugins")|json_encode|raw }}', 'a targeted configuration accessor must not read a hidden subtree');
    }
}
