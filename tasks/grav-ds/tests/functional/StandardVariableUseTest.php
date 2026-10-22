<?php

use CweTests\SandboxTestCase;

/**
 * The standard configuration variables and the targeted settings helper are
 * part of the CMS's legitimate template surface. When configuration reading is
 * enabled and a value is not hidden, content must keep reading it; trusted
 * operator templates must keep their full, unredacted view of the same data.
 *
 * These are the coupled behaviours next to the hidden-value checks: a fix that
 * removes the variables or the helper outright, or that also redacts trusted
 * templates, fails here.
 */
final class StandardVariableUseTest extends SandboxTestCase
{
    private const SITE_SECRET = 'ZZZ_SITE_TRUSTED_SECRET_08f1b4';
    private const THEME_SECRET = 'ZZZ_THEME_TRUSTED_SECRET_c72a90';

    private function enableConfigAccess(): void
    {
        $config = $this->grav['config'];
        $config->set('security.twig_content.config_access', true);
        $config->set('site.title', 'Public Title');
        $config->set('system.param_sep', ':');
        $config->set('theme.dropdown.enabled', 'THEME_DROPDOWN');
        $this->resetSandboxPolicy();
    }

    public function testContentSiteVariableValue(): void
    {
        $this->enableConfigAccess();
        self::assertSame('Public Title', $this->renderPageBody('{{ site.title }}'));
    }

    public function testContentSystemVariableValue(): void
    {
        $this->enableConfigAccess();
        self::assertSame(':', $this->renderPageBody('{{ system.param_sep }}'));
    }

    public function testContentThemeVariableValue(): void
    {
        $this->enableConfigAccess();
        self::assertSame('THEME_DROPDOWN', $this->renderPageBody('{{ theme.dropdown.enabled }}'));
    }

    public function testContentThemeVarHelperValue(): void
    {
        $this->enableConfigAccess();
        self::assertSame('THEME_DROPDOWN', $this->renderPageBody('{{ theme_var("dropdown.enabled") }}'));
    }

    public function testTrustedTemplateSiteVariable(): void
    {
        $this->grav['config']->set('site.integrations.api_key', self::SITE_SECRET);
        $out = $this->renderTrusted('{{ site|json_encode|raw }}');
        self::assertStringContainsString(self::SITE_SECRET, $out, 'trusted templates keep full configuration access');
    }

    public function testTrustedTemplateThemeVarHelper(): void
    {
        $this->grav['config']->set('theme.integrations.api_key', self::THEME_SECRET);
        $out = $this->renderTrusted('{{ theme_var("integrations.api_key") }}');
        self::assertStringContainsString(self::THEME_SECRET, $out, 'trusted templates keep full configuration access');
    }
}
