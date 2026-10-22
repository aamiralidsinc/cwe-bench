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
        self::assertStringContainsString(json_encode($this->header()), $out);
    }

    public function testPageBodyHeaderReflectiveDump(): void
    {
        $out = $this->renderPageBody('{{ header|print_r|raw }}');
        self::assertStringContainsString('[title] => Hello', $out);
        self::assertStringContainsString('[custom_key] => World', $out);
    }

    public function testContentStringHeaderExport(): void
    {
        $out = $this->renderString('{{ header|export|raw }}');
        self::assertStringContainsString("'title' => 'Hello'", $out);
    }

    // --- Editor content: scalar casting/formatting stays usable --------------

    public function testContentScalarExport(): void
    {
        $out = $this->renderString('{{ "snippet"|export|raw }}');
        self::assertSame("'snippet'", $out);
    }

    public function testContentScalarStringCast(): void
    {
        $out = $this->renderPageBody('{{ 123|string }}/{{ header.title|string }}');
        self::assertSame('123/Hello', $out);
    }

    // --- Trusted (theme/plugin) Twig keeps full, unredacted access -----------

    public function testTrustedTemplateSerializesConfig(): void
    {
        $out = $this->renderTrusted('{{ grav.offsetGet("config")|json_encode|raw }}');
        self::assertStringContainsString(self::SECRET_PLUGIN, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplateExportsConfig(): void
    {
        $out = $this->renderTrusted('{{ config|export|raw }}');
        self::assertStringContainsString(self::SECRET_PLUGIN, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplateDumpsConfig(): void
    {
        $out = $this->renderTrusted('{{ config|print_r|raw }}');
        self::assertStringContainsString(self::SECRET_SECURITY, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplateConfigAccessor(): void
    {
        $out = $this->renderTrusted('{{ theme_config("security.salt") }}');
        self::assertStringContainsString(self::SECRET_SECURITY, $out, 'trusted templates keep full config access');
    }

    public function testTrustedTemplateConfigAccessorPrefersThemeSetting(): void
    {
        $this->grav['config']->set('themes.' . self::THEME . '.dropdown.enabled', 'THEME_VALUE');
        $this->grav['config']->set('dropdown.enabled', 'SITE_VALUE');
        $out = $this->renderTrusted('{{ theme_config("dropdown.enabled") }}');
        self::assertSame('THEME_VALUE', $out);
    }
}
