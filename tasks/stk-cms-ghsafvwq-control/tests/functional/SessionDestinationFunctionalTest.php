<?php

namespace CraftTask\Tests\Functional;

use CraftTask\Harness\CraftTestCase;

class SessionDestinationFunctionalTest extends CraftTestCase
{
    public function testLegitimateDestinationsAreStoredAndReturnedUnchanged(): void
    {
        $app = $this->boot();
        $user = $app->getUser();
        $values = [
            'https://test.craftcms.test/adminustriggerus/entries/1?x=1#fragment',
            'https://external.example/after?note=javascript:alert(document.domain)',
            '//test.craftcms.test/adminustriggerus/entries/2',
            '/adminustriggerus/entries/3?y=2#z',
            'dashboard',
            'settings/plugins',
        ];
        foreach ($values as $value) {
            $user->setReturnUrl($value);
            self::assertExactDestination($value, (string)$app->getSession()->get($user->returnUrlParam), 'stored');
            self::assertExactDestination($value, $user->getReturnUrl(), 'returned');
            $user->removeReturnUrl();
        }
    }

    public function testConfiguredCrossSiteDestinationIsHonored(): void
    {
        $app = $this->boot();
        $this->asAdmin();
        $general = $app->getConfig()->getGeneral();
        $general->postCpLoginRedirect = 'https://external.example/after-sign-in';
        $user = $app->getUser();
        $user->removeReturnUrl();
        self::assertExactDestination(
            'https://external.example/after-sign-in',
            $user->getReturnUrl(),
            'configured control-panel destination'
        );
    }
}
