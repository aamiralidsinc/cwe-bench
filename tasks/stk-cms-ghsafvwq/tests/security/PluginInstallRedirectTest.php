<?php

namespace CraftTask\Tests\Security;

use CraftTask\Harness\Actions;
use CraftTask\Harness\CraftTestCase;

/**
 * A plugin may supply the address the browser is sent to when installation finishes. The product
 * reads that address from the plugin's response headers and returns it as the destination.
 */
class PluginInstallRedirectTest extends CraftTestCase
{
    private function request(string $header, string $payload): array
    {
        $app = $this->boot(['task' => 'install'], [], '/adminustriggerus/actions/pluginstore/install/craft-install');
        $this->asAdmin();
        return Actions::installPlugin($app, Actions::installData(), $header, $payload);
    }

    private function assertBlocked(string $header, string $payload): void
    {
        $result = $this->request($header, $payload);
        $state = $result['state'] ?? null;
        $destination = is_array($state) && isset($state['returnUrl']) ? (string)$state['returnUrl'] : null;
        self::assertRefusedOrSafe($result, $destination, 'plugin-supplied destination');
    }

    public function testScriptSchemeFromLocationHeaderNeverSurvives(): void
    {
        $this->assertBlocked('Location', 'javascript://%0Aalert(document.domain)');
    }

    public function testDataUrlFromAlternativeHeaderNeverSurvives(): void
    {
        $this->assertBlocked('X-Redirect', 'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==');
    }
}
