<?php

namespace CraftTask\Tests\Functional;

use CraftTask\Harness\Actions;
use CraftTask\Harness\CraftTestCase;

class PreviewDestinationFunctionalTest extends CraftTestCase
{
    private function request(array $params): array
    {
        $app = $this->boot(['task' => 'preview'], [], '/adminustriggerus/actions/preview/create-token');
        $this->asAdmin();
        return Actions::previewCreateToken($app, $params + [
            'elementType' => 'craft\\elements\\Entry',
            'canonicalId' => '1',
            'siteId' => '1',
        ]);
    }

    public function testLegitimateDestinationsKeepWorking(): void
    {
        $cases = [
            'https://test.craftcms.test/adminustriggerus/entries/1?x=1#fragment'
                => 'https://test.craftcms.test/adminustriggerus/entries/1?x=1#fragment',
            'https://external.example/after?note=javascript:alert(document.domain)'
                => 'https://external.example/after?note=javascript:alert(document.domain)',
            '//test.craftcms.test/adminustriggerus/entries/2'
                => '//test.craftcms.test/adminustriggerus/entries/2',
            '/adminustriggerus/entries/3?y=2#z'
                => 'https://test.craftcms.test/adminustriggerus/entries/3?y=2#z',
        ];
        foreach ($cases as $requested => $expected) {
            $result = $this->request(['redirect' => $requested]);
            self::assertSame(302, $result['status'] ?? 0, 'preview request unexpectedly refused');
            self::assertExactDestination((string)$expected, (string)($result['location'] ?? ''), 'preview destination');
            \craft\test\TestSetup::tearDownCraft();
        }
    }

    public function testRequestWithoutDestinationStillProducesAToken(): void
    {
        $result = $this->request([]);
        self::assertSame(200, $result['status'] ?? 0);
        $data = $result['data'] ?? null;
        self::assertIsArray($data);
        self::assertSame('task-preview-token', $data['token'] ?? null);
    }
}
