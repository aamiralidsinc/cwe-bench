<?php

namespace CraftTask\Tests\Security;

use Craft;
use CraftTask\Harness\Actions;
use CraftTask\Harness\CraftTestCase;

/**
 * The updater family accepts a requested return address in the request body and hands it to the
 * browser in the state it returns.
 */
class UpdaterReturnDestinationTest extends CraftTestCase
{
    private function request(string $returnUrl): array
    {
        $app = $this->boot(['task' => 'updater'], [], '/adminustriggerus/updater/index');
        $this->asAdmin();
        return Actions::updaterIndex($app, ['craft' => Craft::$app->getVersion()], $returnUrl);
    }

    private function assertBlocked(string $payload): void
    {
        $result = $this->request($payload);
        $state = $result['state'] ?? null;
        $destination = is_array($state) && isset($state['returnUrl']) ? (string)$state['returnUrl'] : null;
        self::assertRefusedOrSafe($result, $destination, 'updater return destination');
    }

    public function testScriptSchemeNeverSurvives(): void
    {
        $this->assertBlocked('javascript://%0Aalert(document.domain)');
    }

    public function testScriptSchemeAssembledByMarkupRemovalNeverSurvives(): void
    {
        $this->assertBlocked('java<script></script>script:alert(document.domain)');
    }

    public function testDataUrlNeverSurvives(): void
    {
        $this->assertBlocked('data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==');
    }
}
