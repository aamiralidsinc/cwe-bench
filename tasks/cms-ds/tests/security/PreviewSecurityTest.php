<?php

namespace Tests\Hidden\Security;

require_once __DIR__.'/../support/NavTestCase.php';

use PHPUnit\Framework\Attributes\Test;
use Tests\Hidden\NavTestCase;

class PreviewSecurityTest extends NavTestCase
{
    private function previewUrl(string $id, string $nav = 'test', string $site = 'en')
    {
        return cp_route('navigation.pages.preview', [$nav, $id]).'?site='.$site;
    }

    #[Test]
    public function preview_is_refused_without_permission_to_view_the_navigation()
    {
        $this->hiddenEntry();
        $user = $this->userWith([]);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'hidden-1'],
        ]);

        $response = $this->actingAs($user)->getJson($this->previewUrl('entrypage'));

        $this->assertTrue(
            $response->isClientError(),
            "Expected a client error, got status {$response->status()}"
        );
        $this->assertNotDisclosed($response);
    }

    #[Test]
    public function preview_does_not_disclose_an_entry_the_user_may_not_view()
    {
        $this->hiddenEntry();
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'hidden-1'],
        ]);

        $response = $this->actingAs($user)->getJson($this->previewUrl('entrypage'));

        $this->assertBlocked($response);
    }
}
