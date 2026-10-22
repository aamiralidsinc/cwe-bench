<?php

use CweTests\SandboxTestCase;

/**
 * The redacting `config` variable editor content receives must keep behaving
 * as designed: when reading is enabled, non-sensitive subtrees stay readable
 * while the denied ones are stripped. This is the established behaviour of the
 * feature and must survive any fix. Values and expectations are set up here,
 * not read from product code.
 */
final class ConfigFacadeRegressionTest extends SandboxTestCase
{
    /** Enable config reading for content before the Twig service starts. */
    private function enableConfigAccess(): void
    {
        $config = $this->grav['config'];
        $config->set('security.twig_content.config_access', true);
        $config->set('site.title', 'Public Title');
        $this->resetSandboxPolicy();
    }

    public function testContentReadsAllowedSetting(): void
    {
        $this->enableConfigAccess();
        self::assertSame('Public Title', $this->renderPageBody('{{ config.get("site.title") }}'));
    }

    public function testContentBulkReadStripsDeniedSubtrees(): void
    {
        $this->enableConfigAccess();
        $out = $this->renderString('{{ config.toArray()|json_encode|raw }}');

        self::assertStringContainsString('Public Title', $out, 'allowed config stays readable');
        self::assertStringNotContainsString(self::SECRET_PLUGIN, $out, 'denied subtrees are stripped');
        self::assertStringNotContainsString(self::SECRET_SECURITY, $out, 'denied subtrees are stripped');
    }

    public function testContentPerKeyDeniedReturnsDefault(): void
    {
        $this->enableConfigAccess();
        $out = $this->renderPageBody("{{ config.get('plugins.email.mailer.smtp.password', 'BLOCKED') }}");
        self::assertSame('BLOCKED', $out);
    }
}
