<?php

namespace CraftTask\Tests\Security;

use CraftTask\Harness\Actions;
use CraftTask\Harness\CraftTestCase;

/**
 * The preview-token action accepts a requested address and sends the browser there.
 */
class PreviewRedirectTest extends CraftTestCase
{
    private function request(string $payload): array
    {
        $app = $this->boot(['task' => 'preview'], [], '/adminustriggerus/actions/preview/create-token');
        $this->asAdmin();
        return Actions::previewCreateToken($app, [
            'elementType' => 'craft\\elements\\Entry',
            'canonicalId' => '1',
            'siteId' => '1',
            'redirect' => $payload,
        ]);
    }

    private function assertBlocked(string $payload): void
    {
        $result = $this->request($payload);
        $status = (int)($result['status'] ?? 0);
        self::assertLessThan(500, $status, 'a server error is not a refusal');
        if ($status >= 400) {
            return;
        }
        $location = $result['location'] ?? null;
        if ($location === null) {
            return; // no navigation destination is produced at all
        }
        self::assertSafeDestination((string)$location, 'preview destination');
    }

    public function testScriptSchemeNeverSurvives(): void
    {
        $this->assertBlocked('javascript:alert(document.domain)');
    }

    public function testDataUrlNeverSurvives(): void
    {
        $this->assertBlocked('data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==');
    }
}
