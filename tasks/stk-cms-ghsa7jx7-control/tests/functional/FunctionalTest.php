<?php

use Htest\Harness;
use Htest\MarkerBehavior;
use Htest\ProbeElement;
use Htest\RecordingBehavior;
use Htest\TrustedComponent;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate configuration handling that must keep working.
 */
final class FunctionalTest extends TestCase
{
    protected function setUp(): void
    {
        Harness::reset();
    }

    public function testTrustedComponentConfigurationStillHonoursBehaviors(): void
    {
        $component = \Craft::createObject([
            'class' => TrustedComponent::class,
            'label' => 'trusted',
            'as marker' => ['class' => MarkerBehavior::class],
        ]);

        self::assertInstanceOf(TrustedComponent::class, $component);
        self::assertSame('trusted', $component->label);
        self::assertInstanceOf(MarkerBehavior::class, $component->getBehavior('marker'));
    }

    public function testLayoutSaveStillBuildsNestedStructure(): void
    {
        Harness::request([
            'fieldLayout' => json_encode([
                'type' => 'craft\\elements\\Entry',
                'tabs' => [[
                    'name' => 'Content',
                    'elements' => [[
                        'type' => 'craft\\fieldlayoutelements\\Heading',
                        'heading' => 'A heading',
                    ]],
                ]],
            ]),
        ]);

        $layout = Harness::app()->getFields()->assembleLayoutFromPost();
        self::assertSame('craft\\elements\\Entry', $layout->type);
        $content = null;
        foreach ($layout->getTabs() as $tab) {
            if ($tab->name === 'Content') {
                $content = $tab;
                break;
            }
        }
        self::assertNotNull($content, 'the submitted tab was not kept');
        $headings = array_values(array_filter(
            $content->getElements(),
            fn($element) => $element instanceof \craft\fieldlayoutelements\Heading,
        ));
        self::assertCount(1, $headings);
        self::assertSame('A heading', $headings[0]->heading);
    }

    public function testElementSettingsStillRender(): void
    {
        Harness::request([
            'config' => ['type' => 'craft\\fieldlayoutelements\\Heading'],
            'settingsNamespace' => 'settings',
            'settings' => http_build_query([
                'settings' => ['heading' => 'A heading'],
            ]),
        ]);

        $response = Harness::controller()->actionApplyLayoutElementSettings();
        $data = $response->data;
        self::assertIsArray($data);
        self::assertSame('craft\\fieldlayoutelements\\Heading', $data['config']['type']);
        self::assertSame('A heading', $data['config']['heading']);
        self::assertIsString($data['selectorHtml']);
        self::assertNotSame('', $data['selectorHtml']);
    }

    public function testTabSettingsStillRender(): void
    {
        Harness::request([
            'config' => ['name' => 'Content'],
            'settingsNamespace' => 'settings',
            'settings' => http_build_query([
                'settings' => ['name' => 'Content'],
            ]),
        ]);

        $response = Harness::controller()->actionApplyLayoutTabSettings();
        $data = $response->data;
        self::assertIsArray($data);
        self::assertSame('Content', $data['config']['name']);
        self::assertFalse($data['hasConditions']);
    }

    public function testLayoutFactoryStillBuildsNestedStructure(): void
    {
        $layout = \craft\models\FieldLayout::createFromConfig([
            'type' => 'craft\\elements\\Entry',
            'tabs' => [[
                'name' => 'Content',
                'elements' => [[
                    'type' => 'craft\\fieldlayoutelements\\Heading',
                    'heading' => 'A heading',
                ]],
            ]],
        ]);

        self::assertSame('craft\\elements\\Entry', $layout->type);
        $content = null;
        foreach ($layout->getTabs() as $tab) {
            if ($tab->name === 'Content') {
                $content = $tab;
                break;
            }
        }
        self::assertNotNull($content, 'the configured tab was not kept');
        $headings = array_values(array_filter(
            $content->getElements(),
            fn($element) => $element instanceof \craft\fieldlayoutelements\Heading,
        ));
        self::assertCount(1, $headings);
    }

    public function testTabFactoryStillBuildsTab(): void
    {
        $layout = \craft\models\FieldLayout::createFromConfig([
            'type' => 'craft\\elements\\Entry',
        ]);
        $tab = \craft\models\FieldLayoutTab::createFromConfig([
            'layout' => $layout,
            'name' => 'Content',
            'sortOrder' => 3,
        ]);

        self::assertSame('Content', $tab->name);
        self::assertSame(3, $tab->sortOrder);
    }

    public function testDuplicationStillAttachesSuppliedBehavior(): void
    {
        $element = new ProbeElement(['id' => 1, 'siteId' => 1]);
        $behavior = new RecordingBehavior();

        try {
            Harness::app()->getElements()->duplicateElement($element, [
                'title' => 'Duplicated title',
                'behaviors' => ['draft' => $behavior],
            ]);
        } catch (\Throwable) {
            // The fixture element cannot be saved; the behavior block runs first.
        }

        self::assertCount(1, RecordingBehavior::$attached);
        self::assertSame('Duplicated title', RecordingBehavior::$attached[0]['title']);
    }
}
