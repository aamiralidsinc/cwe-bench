<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use craft\elements\conditions\entries\EntryCondition;
use craft\elements\conditions\users\UserCondition;
use craft\fieldlayoutelements\Template;
use craft\helpers\Json;
use craft\models\FieldLayout;
use CraftBench\Harness;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate posted layouts keep their tabs, template elements, widths and conditions.
 */
class PostedLayoutFunctionalTest extends TestCase
{
    private function assemble(array $layout): FieldLayout
    {
        $request = new \craft\web\Request();
        $request->setBodyParams(['fieldLayout' => Json::encode($layout)]);
        Harness::$app->set('request', $request);
        return Harness::$app->getFields()->assembleLayoutFromPost();
    }

    private function assertTemplateElement(array $layout): void
    {
        $fieldLayout = $this->assemble($layout);
        $tabs = $fieldLayout->getTabs();
        $this->assertCount(1, $tabs);
        $this->assertSame('Content', $tabs[0]->name);

        $elements = $tabs[0]->getElements();
        $this->assertCount(1, $elements);
        $element = $elements[0];
        $this->assertInstanceOf(Template::class, $element);
        $this->assertSame('_layout-elements/info', $element->template);
        $this->assertSame(50, $element->width);

        $userCondition = $element->getUserCondition();
        $this->assertInstanceOf(UserCondition::class, $userCondition);
        $this->assertCount(1, $userCondition->getConditionRules());

        $elementCondition = $element->getElementCondition();
        $this->assertInstanceOf(EntryCondition::class, $elementCondition);
        $this->assertCount(1, $elementCondition->getConditionRules());
    }

    public function testLegitArrayLayoutIsAssembled(): void
    {
        $this->assertTemplateElement(Harness::legitLayout());
    }

    public function testLegitEncodedElementsAreAssembled(): void
    {
        $this->assertTemplateElement(Harness::legitLayout(true));
    }

    public function testEntryTypeWithLegitLayoutSaves(): void
    {
        $handle = 'craftBenchSave' . substr(bin2hex(random_bytes(4)), 0, 6);
        $error = Harness::postEntryTypeLayout(Harness::legitLayout(), $handle);
        $this->assertNull($error, 'a legitimate layout could not be saved');

        $entryType = null;
        foreach (Harness::$app->getSections()->getEntryTypesBySectionId(Harness::$section->id) as $candidate) {
            if ($candidate->handle === $handle) {
                $entryType = $candidate;
                break;
            }
        }
        $this->assertNotNull($entryType, 'the saved entry type was not found');

        $layout = $entryType->getFieldLayout();
        $this->assertNotNull($layout);
        $templates = [];
        foreach ($layout->getTabs() as $tab) {
            foreach ($tab->getElements() as $element) {
                if ($element instanceof Template) {
                    $templates[] = $element;
                }
            }
        }
        $this->assertCount(1, $templates);
        $this->assertSame('_layout-elements/info', $templates[0]->template);
        $this->assertSame(50, $templates[0]->width);
    }
}
