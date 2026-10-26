<?php

namespace Tests\Hidden\Functional;

require_once __DIR__.'/../support/NavTestCase.php';

use PHPUnit\Framework\Attributes\Test;
use Tests\Hidden\NavTestCase;

class PreviewFunctionalTest extends NavTestCase
{
    #[Test]
    public function preview_returns_the_page_and_entry_values_for_a_user_who_may_view_them()
    {
        $this->visibleEntry();
        $user = $this->userWith(['view test nav', 'view articles entries']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'visible-1'],
        ]);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.preview', ['test', 'entrypage']).'?site=en'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['VISIBLE-TITLE-ABC', 'VISIBLE-FOO-ABC']);
    }

    #[Test]
    public function preview_returns_a_url_page_for_a_user_who_may_view_the_navigation()
    {
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', [
            ['id' => 'urlpage', 'title' => 'PREVIEW-URL-TITLE', 'url' => '/preview-url'],
        ]);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.preview', ['test', 'urlpage']).'?site=en'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['PREVIEW-URL-TITLE']);
    }
}
