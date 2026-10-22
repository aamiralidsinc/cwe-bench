<?php

use CweTests\SandboxTestCase;

/**
 * Coupled behaviour for the theme settings views. When only a specific theme
 * setting is hidden, the rest of the theme settings surface must keep working
 * for content through every documented view, page-header values must keep
 * taking precedence in theme_var(), and trusted templates keep the raw view.
 */
final class ThemeSettingsAliasUseTest extends SandboxTestCase
{
    private const SECRET = 'ZZZ_THEME_ALIAS_TRUSTED_5d0e';
    private const ALLOWED = 'THEME_ALLOWED_VALUE';

    protected function setUp(): void
    {
        parent::setUp();
        $config = $this->grav['config'];
        $config->set('themes.' . self::THEME . '.integrations.api_key', self::SECRET);
        $config->set('themes.' . self::THEME . '.dropdown.enabled', self::ALLOWED);
        // The application copies the stored theme settings onto the legacy
        // `theme` key when it initialises the active theme.
        $this->grav['themes']->load();
        $config->set('security.twig_content.config_access', true);
        $denied = (array) $config->get('security.twig_sandbox.config_denied_paths', []);
        $denied[] = 'themes.' . self::THEME . '.integrations';
        $config->set('security.twig_sandbox.config_denied_paths', array_values(array_unique($denied)));
        $this->resetSandboxPolicy();
    }

    public function testContentThemeVariableAllowedValue(): void
    {
        self::assertSame(self::ALLOWED, $this->renderPageBody('{{ theme.dropdown.enabled }}'));
    }

    public function testContentThemeVarAllowedValue(): void
    {
        self::assertSame(self::ALLOWED, $this->renderPageBody('{{ theme_var("dropdown.enabled") }}'));
    }

    public function testContentThemeConfigAllowedValue(): void
    {
        self::assertSame(self::ALLOWED, $this->renderPageBody('{{ theme_config("dropdown.enabled") }}'));
    }

    public function testContentThemeVarPrefersPageHeader(): void
    {
        self::assertSame('World', $this->renderPageBody('{{ theme_var("custom_key") }}'));
    }

    public function testTrustedThemeVarKeepsRawView(): void
    {
        $out = $this->renderTrusted('{{ theme_var("integrations.api_key") }}');
        self::assertStringContainsString(self::SECRET, $out, 'trusted templates keep full configuration access');
    }

    public function testTrustedThemeVariableKeepsRawView(): void
    {
        $out = $this->renderTrusted('{{ theme|json_encode|raw }}');
        self::assertStringContainsString(self::SECRET, $out, 'trusted templates keep full configuration access');
    }
}
