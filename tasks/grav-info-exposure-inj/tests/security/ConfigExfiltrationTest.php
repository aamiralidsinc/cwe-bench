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

    public function testSerializeContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|json_encode|raw }}', 'serializing a container-reached config must not leak');
    }

    public function testReflectContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|print_r|raw }}', 'reflective dump of a container-reached config must not leak');
    }

    public function testYamlContainerConfig(): void
    {
        $this->assertNoSecret('{{ grav.offsetGet("config")|yaml_encode|raw }}', 'yaml dump of a container-reached config must not leak');
    }

    public function testReflectConfigVariable(): void
    {
        $this->assertNoSecret('{{ config|print_r|raw }}', 'reflective dump of the config variable must not expose its hidden state');
    }

    public function testExportConfigVariable(): void
    {
        $this->assertNoSecret('{{ config|export|raw }}', 'exporting the config variable must not expose its hidden state');
    }

    public function testDebugDumpConfigVariable(): void
    {
        $this->assertNoSecret('{{ vardump(config) }}', 'debug-dumping the config variable must not expose its hidden state');
    }

    public function testConfigAccessorScalar(): void
    {
        $this->assertNoSecret('{{ theme_config("security.salt") }}', 'a configuration accessor must not read a hidden value');
    }

    public function testConfigAccessorSubtree(): void
    {
        $this->assertNoSecret('{{ theme_config("plugins")|json_encode|raw }}', 'a configuration accessor must not read a hidden subtree');
    }

    public function testSerializeArrayHoldingConfig(): void
    {
        $this->assertNoSecret('{{ [grav.offsetGet("config")]|string|raw }}', 'serializing a list that holds a config object must not leak');
    }

    public function testReflectListHoldingConfig(): void
    {
        $this->assertNoSecret('{{ ["x", config]|print_r|raw }}', 'dumping a list that holds the config variable must not leak');
    }

    public function testExportObjectCarryingConfig(): void
    {
        $this->assertNoSecret('{{ grav.theme|export|raw }}', 'exporting an object that carries the configuration must not leak');
    }
}
