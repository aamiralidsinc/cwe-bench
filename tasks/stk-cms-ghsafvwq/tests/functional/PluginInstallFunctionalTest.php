<?php

namespace CraftTask\Tests\Functional;

use CraftTask\Harness\Actions;
use CraftTask\Harness\CraftTestCase;

class PluginInstallFunctionalTest extends CraftTestCase
{
    private function request(?string $header, ?string $value, ?string $returnUrl = 'settings/plugins'): array
    {
        $app = $this->boot(['task' => 'install'], [], '/adminustriggerus/actions/pluginstore/install/craft-install');
        $this->asAdmin();
        $data = Actions::installData();
        if ($returnUrl === null) {
            unset($data['returnUrl']);
        } else {
            $data['returnUrl'] = $returnUrl;
        }
        return Actions::installPlugin($app, $data, $header, $value);
    }

    public function testPluginSuppliedDestinationsKeepWorking(): void
    {
        foreach ([
            'https://plugins.example/after-install?step=2',
            'https://external.example/after?note=javascript:alert(document.domain)',
            'settings/plugins',
            'plugin-store',
        ] as $value) {
            $result = $this->request('Location', $value);
            self::assertSame(200, $result['status'] ?? 0, 'install request unexpectedly refused');
            $state = $result['state'] ?? null;
            self::assertIsArray($state);
            self::assertExactDestination($value, (string)$state['returnUrl'], 'plugin-supplied destination');
            \craft\test\TestSetup::tearDownCraft();
        }
    }

    public function testWhitelistedPostedDestinationIsUsedWithoutAPluginDestination(): void
    {
        $result = $this->request(null, null, 'settings/plugins');
        self::assertSame(200, $result['status'] ?? 0);
        $state = $result['state'] ?? null;
        self::assertIsArray($state);
        self::assertExactDestination('settings/plugins', (string)$state['returnUrl'], 'posted destination');
    }

    public function testDefaultDestinationIsUsedWhenNoneIsSupplied(): void
    {
        $result = $this->request(null, null, null);
        self::assertSame(200, $result['status'] ?? 0);
        $state = $result['state'] ?? null;
        self::assertIsArray($state);
        self::assertExactDestination('plugin-store', (string)$state['returnUrl'], 'default destination');
    }
}
