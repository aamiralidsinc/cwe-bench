<?php

use CweTests\SandboxTestCase;

/**
 * Legitimate uses that must keep working exactly as before a fix. These guard
 * against an over-broad fix that disables dumping/serialization outright, blocks
 * plain page-header data, breaks value casts, or leaks into trusted templates.
 */
final class LegitimateUseTest extends SandboxTestCase
{
    // --- Editor content: plain page-header data stays fully usable -----------

    public function testPageBodyHeaderJsonEncode(): void
    {
        $out = $this->renderPageBody('{{ header|json_encode|raw }}');
        self::assertStringContainsString('"title":"Hello"', $out);
        self::assertStringContainsString('"custom_key":"World"', $out);
    }

    public function testPageBodyHeaderReflectiveDump(): void
    {
        $out = $this->renderPageBody('{{ header|print_r|raw }}');
        self::assertStringContainsString('[title] => Hello', $out);
        self::assertStringContainsString('[custom_key] => World', $out);
    }

    public function testPageBodyHeaderArrayJson(): void
    {
        $out = $this->renderPageBody('{{ header|array|json_encode|raw }}');
        self::assertStringContainsString('"title":"Hello"', $out);
    }

    public function testPageBodyHeaderYaml(): void
    {
        $out = $this->renderPageBody('{{ header|array|yaml|raw }}');
        self::assertStringContainsString('title: Hello', $out);
    }

    public function testPageBodyHeaderPrettyJson(): void
    {
        $out = $this->renderPageBody('{{ header|to_json|raw }}');
        self::assertStringContainsString('"title": "Hello"', $out);
    }

    public function testPageBodyHeaderInspect(): void
    {
        $out = $this->renderPageBody('{{ inspect(header)|raw }}');
        self::assertStringContainsString('[title] => Hello', $out);
    }

    // --- Editor content: scalar casting/formatting stays usable --------------

    public function testContentScalarStringCast(): void
    {
        $out = $this->renderString('{{ 123|string }}/{{ header.title|string }}');
        self::assertSame('123/Hello', $out);
    }

    public function testContentListYaml(): void
    {
        $out = $this->renderString('{{ [1,2,3]|yaml|raw }}');
        self::assertStringContainsString('- 1', $out);
    }

    public function testContentListArrayJson(): void
    {
        $out = $this->renderString('{{ [1,2,3]|array|json_encode|raw }}');
        self::assertSame('[1,2,3]', $out);
    }

    // --- Editor content: the redacting config facade stays usable -----------

    public function testContentFacadeYamlEncode(): void
    {
        $out = $this->renderString('{{ config|yaml_encode|raw }}');
        self::assertStringNotContainsString(self::SECRET_PLUGIN, $out);
        self::assertStringNotContainsString(self::SECRET_SECURITY, $out);
    }

    public function testContentFacadeArrayJson(): void
    {
        $out = $this->renderString('{{ config|array|json_encode|raw }}');
        self::assertStringNotContainsString(self::SECRET_PLUGIN, $out);
        self::assertStringNotContainsString(self::SECRET_SECURITY, $out);
    }

    public function testContentFacadeJsonEncode(): void
    {
        $out = $this->renderString('{{ config|json_encode|raw }}');
        self::assertStringNotContainsString(self::SECRET_PLUGIN, $out);
        self::assertStringNotContainsString(self::SECRET_SECURITY, $out);
    }

    // --- Trusted (theme/plugin) Twig keeps full, unredacted access -----------

    public function testTrustedTemplateSerializesConfig(): void
    {
        $out = $this->renderTrusted('{{ grav.offsetGet("config")|json_encode|raw }}');
        self::assertStringContainsString(self::SECRET_PLUGIN, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplateReflectsConfig(): void
    {
        $out = $this->renderTrusted('{{ config|print_r|raw }}');
        self::assertStringContainsString(self::SECRET_SECURITY, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplatePrettyJson(): void
    {
        $out = $this->renderTrusted('{{ to_json(grav.offsetGet("config"))|raw }}');
        self::assertStringContainsString(self::SECRET_PLUGIN, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplateInspect(): void
    {
        $out = $this->renderTrusted('{{ inspect(grav.offsetGet("config"))|raw }}');
        self::assertStringContainsString(self::SECRET_SECURITY, $out, 'trusted templates keep full config access');
    }
}
