<?php

use Htest\Harness;
use Htest\MarkerBehavior;
use PHPUnit\Framework\TestCase;

/**
 * The layout-save service must not honour class-bearing configuration keys,
 * at the top level, in a namespaced submission, or nested in a tab or element.
 */
final class LayoutSaveSecurityTest extends TestCase
{
    protected function setUp(): void
    {
        Harness::reset();
    }

    public function testTopLevelConfigurationCannotAttachBehavior(): void
    {
        Harness::request([
            'fieldLayout' => json_encode([
                'type' => 'craft\\elements\\Entry',
                'as marker' => ['class' => MarkerBehavior::class],
            ]),
        ]);

        try {
            Harness::app()->getFields()->assembleLayoutFromPost();
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the layout configuration constructed a named class');
    }

    public function testNamespacedConfigurationCannotAttachBehavior(): void
    {
        Harness::request([
            'fields.fieldLayout' => json_encode([
                'type' => 'craft\\elements\\Entry',
                'as marker' => ['class' => MarkerBehavior::class],
            ]),
        ]);

        try {
            Harness::app()->getFields()->assembleLayoutFromPost('fields');
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the namespaced layout configuration constructed a named class');
    }

    public function testNestedTabConfigurationCannotAttachBehavior(): void
    {
        Harness::request([
            'fieldLayout' => json_encode([
                'type' => 'craft\\elements\\Entry',
                'tabs' => [[
                    'name' => 'Content',
                    'as marker' => ['class' => MarkerBehavior::class],
                ]],
            ]),
        ]);

        try {
            Harness::app()->getFields()->assembleLayoutFromPost();
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'a nested tab configuration constructed a named class');
    }

    public function testNestedElementConfigurationCannotAttachBehavior(): void
    {
        Harness::request([
            'fieldLayout' => json_encode([
                'type' => 'craft\\elements\\Entry',
                'tabs' => [[
                    'name' => 'Content',
                    'elements' => [[
                        'type' => 'craft\\fieldlayoutelements\\Heading',
                        'as marker' => ['class' => MarkerBehavior::class],
                    ]],
                ]],
            ]),
        ]);

        try {
            Harness::app()->getFields()->assembleLayoutFromPost();
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'a nested element configuration constructed a named class');
    }
}
