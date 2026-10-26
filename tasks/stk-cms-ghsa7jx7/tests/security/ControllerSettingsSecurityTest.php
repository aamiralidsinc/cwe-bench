<?php

use Htest\Harness;
use Htest\MarkerBehavior;
use PHPUnit\Framework\TestCase;

/**
 * The control-panel field layout settings actions must not honour
 * class-bearing configuration keys, whether they arrive in the main
 * configuration or in the settings namespace.
 */
final class ControllerSettingsSecurityTest extends TestCase
{
    protected function setUp(): void
    {
        Harness::reset();
    }

    public function testElementActionConfigurationCannotAttachBehavior(): void
    {
        Harness::request([
            'config' => [
                'type' => 'craft\\fieldlayoutelements\\Heading',
                'as marker' => ['class' => MarkerBehavior::class],
            ],
            'settingsNamespace' => 'settings',
            'settings' => '',
        ]);

        try {
            Harness::controller()->actionApplyLayoutElementSettings();
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the element settings action constructed a named class');
    }

    public function testElementActionSettingsNamespaceCannotAttachBehavior(): void
    {
        Harness::request([
            'config' => ['type' => 'craft\\fieldlayoutelements\\Heading'],
            'settingsNamespace' => 'settings',
            'settings' => http_build_query([
                'settings' => [
                    'as marker' => ['class' => MarkerBehavior::class],
                ],
            ]),
        ]);

        try {
            Harness::controller()->actionApplyLayoutElementSettings();
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the settings namespace constructed a named class');
    }

    public function testTabActionConfigurationCannotAttachBehavior(): void
    {
        Harness::request([
            'config' => [
                'name' => 'Content',
                'as marker' => ['class' => MarkerBehavior::class],
            ],
            'settingsNamespace' => 'settings',
            'settings' => '',
        ]);

        try {
            Harness::controller()->actionApplyLayoutTabSettings();
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the tab settings action constructed a named class');
    }
}
