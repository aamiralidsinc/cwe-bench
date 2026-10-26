<?php

namespace CraftTask\Tests\Functional;

use Craft;
use CraftTask\Harness\Actions;
use CraftTask\Harness\CraftTestCase;

class UpdaterDestinationFunctionalTest extends CraftTestCase
{
    private function request(?string $returnUrl): array
    {
        $app = $this->boot(['task' => 'updater'], [], '/adminustriggerus/updater/index');
        $this->asAdmin();
        return Actions::updaterIndex($app, ['craft' => Craft::$app->getVersion()], $returnUrl);
    }

    public function testLegitimateDestinationsPassThrough(): void
    {
        $values = [
            'https://test.craftcms.test/adminustriggerus/entries/1?x=1#fragment',
            'https://external.example/after?note=javascript:alert(document.domain)',
            '//test.craftcms.test/adminustriggerus/entries/2',
            '/adminustriggerus/entries/3?y=2#z',
            'dashboard',
            'settings/plugins',
        ];
        foreach ($values as $value) {
            $result = $this->request($value);
            self::assertSame(200, $result['status'] ?? 0, 'updater request unexpectedly refused');
            $state = $result['state'] ?? null;
            self::assertIsArray($state);
            self::assertExactDestination($value, (string)$state['returnUrl'], 'updater destination');
            \craft\test\TestSetup::tearDownCraft();
        }
    }

    public function testConfiguredDestinationIsUsedWhenNoneIsSupplied(): void
    {
        $app = $this->boot(['task' => 'updater'], [], '/adminustriggerus/updater/index');
        $this->asAdmin();
        $result = Actions::updaterIndex($app, ['craft' => Craft::$app->getVersion()], null);
        self::assertSame(200, $result['status'] ?? 0);
        $state = $result['state'] ?? null;
        self::assertIsArray($state);
        self::assertExactDestination(
            $app->getConfig()->getGeneral()->getPostCpLoginRedirect(),
            (string)$state['returnUrl'],
            'configured updater destination'
        );
    }
}
