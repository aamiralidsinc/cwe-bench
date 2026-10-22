<?php

use CweTests\SandboxTestCase;

/**
 * Coupled behaviour for the container views content legitimately uses. The
 * container accessor is closed to content, but the value-free members the
 * application deliberately allows must keep working, and trusted templates
 * must keep their full view of the container and its configuration service.
 */
final class ContainerSelfAliasUseTest extends SandboxTestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        $config = $this->grav['config'];
        $config->set('security.twig_content.config_access', true);
        $this->resetSandboxPolicy();
    }

    public function testContentContainerVersion(): void
    {
        $out = $this->renderPageBody('{{ grav.getversion }}');
        self::assertMatchesRegularExpression('/^\d+\.\d+/', trim($out), 'the allowed container version member keeps working for content');
    }

    public function testContentContainerOffsetExists(): void
    {
        self::assertSame('yes', $this->renderPageBody('{{ grav.offsetExists("config") ? "yes" : "no" }}'));
    }

    public function testTrustedTemplateRawContainerConfig(): void
    {
        $out = $this->renderTrusted('{{ grav.offsetGet("config").get("security.salt") }}');
        self::assertStringContainsString(self::SECRET_SECURITY, $out, 'trusted templates keep full container access');
    }
}
