<?php

use Htest\Harness;
use Htest\MarkerBehavior;
use PHPUnit\Framework\TestCase;

/**
 * The field layout config factories must not honour class-bearing
 * configuration keys, at the top level or inside nested tab/element config.
 */
final class FactorySecurityTest extends TestCase
{
    protected function setUp(): void
    {
        Harness::reset();
    }

    public function testLayoutFactoryCannotAttachBehavior(): void
    {
        try {
            \craft\models\FieldLayout::createFromConfig([
                'type' => 'craft\\elements\\Entry',
                'as marker' => ['class' => MarkerBehavior::class],
            ]);
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the layout factory constructed a named class');
    }

    public function testLayoutFactoryNestedTabCannotAttachBehavior(): void
    {
        try {
            \craft\models\FieldLayout::createFromConfig([
                'type' => 'craft\\elements\\Entry',
                'tabs' => [[
                    'name' => 'Content',
                    'as marker' => ['class' => MarkerBehavior::class],
                ]],
            ]);
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the layout factory constructed a class named inside a tab');
    }

    public function testLayoutFactoryNestedElementCannotAttachBehavior(): void
    {
        try {
            \craft\models\FieldLayout::createFromConfig([
                'type' => 'craft\\elements\\Entry',
                'tabs' => [[
                    'name' => 'Content',
                    'elements' => [[
                        'type' => 'craft\\fieldlayoutelements\\Heading',
                        'as marker' => ['class' => MarkerBehavior::class],
                    ]],
                ]],
            ]);
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the layout factory constructed a class named inside an element');
    }

    public function testTabFactoryCannotAttachBehavior(): void
    {
        try {
            \craft\models\FieldLayoutTab::createFromConfig([
                'name' => 'Content',
                'as marker' => ['class' => MarkerBehavior::class],
            ]);
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }

        self::assertSame(0, MarkerBehavior::$instances, 'the tab factory constructed a named class');
    }
}
