<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use craft\elements\conditions\entries\EntryCondition;
use craft\elements\conditions\users\UserCondition;
use craft\elements\User;
use craft\fieldlayoutelements\Template;
use craft\helpers\StringHelper;
use CraftBench\Harness;
use PHPUnit\Framework\TestCase;

/**
 * A legitimate layout applied from the project's configuration keeps its values.
 */
class ProjectConfigLayoutFunctionalTest extends TestCase
{
    public function testConfiguredLayoutKeepsItsValues(): void
    {
        $uid = StringHelper::UUID();
        try {
            Harness::setProjectConfig('users.fieldLayouts', [
                $uid => Harness::legitLayout(),
            ]);
        } catch (\Throwable $e) {
            $this->fail('a legitimate configured layout could not be applied: ' . $e->getMessage());
        }

        $layout = Harness::$app->getFields()->getLayoutByType(User::class);
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
        $template = $templates[0];
        $this->assertSame('_layout-elements/info', $template->template);
        $this->assertSame(50, $template->width);

        $userCondition = $template->getUserCondition();
        $this->assertInstanceOf(UserCondition::class, $userCondition);
        $this->assertCount(1, $userCondition->getConditionRules());

        $elementCondition = $template->getElementCondition();
        $this->assertInstanceOf(EntryCondition::class, $elementCondition);
        $this->assertCount(1, $elementCondition->getConditionRules());
    }
}
