<?php

use CweTests\SandboxTestCase;

/**
 * The active theme's settings live under the configuration's `themes.<name>`
 * subtree and the application also keeps a `theme` copy of the same data,
 * which is what the standard `theme` variable, theme_var() and the config
 * lookup fallback read. When the site marks the stored theme settings subtree
 * denied, that hidden value must not become visible through the copy view.
 *
 * Values and expectations are seeded here, not read from product code; any
 * refusal form is accepted.
 */
final class ThemeSettingsAliasTest extends SandboxTestCase
{
    private const SECRET = 'ZZZ_THEME_ALIAS_SECRET_c41f';
    private const ALLOWED = 'THEME_ALLOWED_VALUE';

    protected function setUp(): void
    {
        parent::setUp();

        $config = $this->grav['config'];
        // The stored settings, exactly where a theme's settings YAML lands.
        $config->set('themes.' . self::THEME . '.integrations.api_key', self::SECRET);
        $config->set('themes.' . self::THEME . '.dropdown.enabled', self::ALLOWED);
        // Initialise the active theme through the application, which copies
        // the stored settings onto the legacy `theme` key (Themes::load()).
        $this->grav['themes']->load();

        $config->set('security.twig_content.config_access', true);
        $denied = (array) $config->get('security.twig_sandbox.config_denied_paths', []);
        $denied[] = 'themes.' . self::THEME . '.integrations';
        $config->set('security.twig_sandbox.config_denied_paths', array_values(array_unique($denied)));
        $this->resetSandboxPolicy();
    }

    private function assertHidden(string $template, string $context): void
    {
        $out = $this->renderContent($template);
        self::assertFalse(str_contains($out, self::SECRET), $context . ' (hidden value reached the page)');
    }

    // --- the theme variable (copy of the active theme's settings) -----------

    public function testThemeVariableDirectRead(): void
    {
        $this->assertHidden('{{ theme.integrations.api_key }}', 'reading a denied theme setting from the theme variable must not leak');
    }

    public function testThemeVariableBulk(): void
    {
        $this->assertHidden('{{ theme|json_encode|raw }}', 'serialising the theme variable must not leak a denied theme setting');
    }

    public function testThemeVariableInsideList(): void
    {
        $this->assertHidden('{{ [theme]|print_r|raw }}', 'dumping a list holding the theme variable must not leak');
    }

    // --- targeted theme-settings helpers -----------------------------------

    public function testThemeVarHelper(): void
    {
        $this->assertHidden('{{ theme_var("integrations.api_key") }}', 'the theme settings helper must not read a denied setting');
    }

    public function testHeaderVarHelper(): void
    {
        $this->assertHidden('{{ header_var("integrations.api_key") }}', 'the deprecated header helper must not read a denied setting');
    }

    public function testThemeConfigHelper(): void
    {
        $this->assertHidden('{{ theme_config("integrations.api_key") }}', 'the config lookup helper must not read a denied theme setting');
    }

    public function testThemeConfigHelperThroughCopyPath(): void
    {
        $this->assertHidden(
            '{{ theme_config("theme.integrations.api_key") }}',
            'the config lookup fallback must not read the legacy copy of a denied theme setting'
        );
    }
}
