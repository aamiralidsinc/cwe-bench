<?php

use CweTests\SandboxTestCase;

/**
 * The render environment also hands editor content the standard configuration
 * variables (`site`, `system`, `theme`). A subtree the operator has hidden from
 * content must stay hidden no matter which of those views it is read through,
 * and no matter whether it is read directly, serialised, or reflectively
 * dumped.
 *
 * Each case enables content configuration reading, marks a subtree denied, and
 * renders through both content entry points. Any refusal form is accepted; the
 * tests look only at what was rendered.
 */
final class StandardVariableExfiltrationTest extends SandboxTestCase
{
    private const SITE_SECRET = 'ZZZ_SITE_SECRET_41d7a2';
    private const SYSTEM_SECRET = 'ZZZ_SYSTEM_SECRET_9c3e88';
    private const THEME_SECRET = 'ZZZ_THEME_SECRET_2b6f15';

    protected function setUp(): void
    {
        parent::setUp();

        $config = $this->grav['config'];
        $config->set('site.integrations.api_key', self::SITE_SECRET);
        $config->set('system.integrations.api_key', self::SYSTEM_SECRET);
        $config->set('theme.integrations.api_key', self::THEME_SECRET);
        $config->set('site.title', 'Public Title');
        $config->set('theme.dropdown.enabled', 'THEME_DROPDOWN');
        $this->resetSandboxPolicy();
    }

    private function enableConfigAccess(array $denied): void
    {
        $config = $this->grav['config'];
        $config->set('security.twig_content.config_access', true);
        $current = (array) $config->get('security.twig_sandbox.config_denied_paths', []);
        $config->set('security.twig_sandbox.config_denied_paths', array_values(array_unique(array_merge($current, $denied))));
        $this->resetSandboxPolicy();
    }

    private function assertHidden(string $template, string $context, string $secret): void
    {
        $out = $this->renderContent($template);
        self::assertFalse(str_contains($out, $secret), $context . ' (hidden value reached the page)');
    }

    public function testSiteVariableBulk(): void
    {
        $this->enableConfigAccess(['site.integrations']);
        $this->assertHidden('{{ site|json_encode|raw }}', 'serialising the site variable must not leak a denied value', self::SITE_SECRET);
    }

    public function testSiteVariableDirectRead(): void
    {
        $this->enableConfigAccess(['site.integrations']);
        $this->assertHidden('{{ site.integrations.api_key }}', 'reading a denied value from the site variable must not leak', self::SITE_SECRET);
    }

    public function testSiteVariableReflectiveDump(): void
    {
        $this->enableConfigAccess(['site.integrations']);
        $this->assertHidden('{{ site|print_r|raw }}', 'dumping the site variable must not leak a denied value', self::SITE_SECRET);
    }

    public function testSiteVariableInsideList(): void
    {
        $this->enableConfigAccess(['site.integrations']);
        $this->assertHidden('{{ [site]|json_encode|raw }}', 'serialising a list holding the site variable must not leak', self::SITE_SECRET);
    }

    public function testSystemVariableBulk(): void
    {
        $this->enableConfigAccess(['system.integrations']);
        $this->assertHidden('{{ system|json_encode|raw }}', 'a denied system subtree must not reappear through the system variable', self::SYSTEM_SECRET);
    }

    public function testSystemVariableDirectRead(): void
    {
        $this->enableConfigAccess(['system.integrations']);
        $this->assertHidden('{{ system.integrations.api_key }}', 'reading a denied value from the system variable must not leak', self::SYSTEM_SECRET);
    }

    public function testThemeVariableBulk(): void
    {
        $this->enableConfigAccess(['theme.integrations']);
        $this->assertHidden('{{ theme|json_encode|raw }}', 'a denied theme subtree must not reappear through the theme variable', self::THEME_SECRET);
    }
}
