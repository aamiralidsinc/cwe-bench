<?php

use CweTests\SandboxTestCase;

/**
 * The container registered by the application exposes itself under its own
 * service id (`grav`). Content that walks the container with the read accessor
 * must not be able to take that self-reference and use it to reach the raw
 * configuration service, which the container accessor otherwise hands out only
 * through the redacted view.
 *
 * The tests enable content configuration reading (so the configuration
 * service's own methods are part of the content surface at all) and assert
 * that the marker secret hidden by the default `security` denial never reaches
 * the page. Any refusal form is accepted.
 */
final class ContainerSelfAliasTest extends SandboxTestCase
{
    

    protected function setUp(): void
    {
        parent::setUp();
        $config = $this->grav['config'];
        $config->set('security.twig_content.config_access', true);
        $this->resetSandboxPolicy();
    }

    private function assertHidden(string $template, string $context): void
    {
        $out = $this->renderContent($template);
        self::assertFalse(str_contains($out, self::SECRET_SECURITY), $context . ' (hidden value reached the page)');
    }

    public function testSelfAliasMethodChain(): void
    {
        $this->assertHidden(
            '{{ grav.offsetGet("grav").offsetGet("config").get("security.salt") }}',
            'walking the container through its own service id must not reach the raw configuration'
        );
    }

    public function testSelfAliasAttributeChain(): void
    {
        $this->assertHidden(
            '{{ attribute(attribute(grav, "offsetGet", ["grav"]), "offsetGet", ["config"]).get("security.salt") }}',
            'the attribute() spelling must not reach the raw configuration either'
        );
    }

    public function testSelfAliasValueMethod(): void
    {
        $this->assertHidden(
            '{{ grav.offsetGet("grav").offsetGet("config").value("security.salt") }}',
            'the alternative value accessor must not read a hidden value'
        );
    }

    public function testSelfAliasWholeTree(): void
    {
        $this->assertHidden(
            '{{ grav.offsetGet("grav").offsetGet("config").get("")|json_encode|raw }}',
            'the self alias must not expose the whole configuration tree'
        );
    }
}
