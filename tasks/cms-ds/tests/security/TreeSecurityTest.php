<?php

namespace Tests\Hidden\Security;

require_once __DIR__.'/../support/NavTestCase.php';

use PHPUnit\Framework\Attributes\Test;
use Tests\Hidden\NavTestCase;

class TreeSecurityTest extends NavTestCase
{
    private function indexUrl(string $nav = 'test', string $site = 'en')
    {
        return cp_route('navigation.tree.index', $nav).'?site='.$site;
    }

    #[Test]
    public function tree_is_refused_without_permission_to_view_the_navigation()
    {
        $user = $this->userWith([]);
        $this->makeNav('test', [
            ['id' => 'urlpage', 'title' => 'NAV-PAGE-MARKER', 'url' => '/nav-page'],
        ]);

        $response = $this->actingAs($user)->getJson($this->indexUrl());

        $this->assertTrue(
            $response->isClientError(),
            "Expected a client error, got status {$response->status()}"
        );
        $this->assertStringNotContainsString('NAV-PAGE-MARKER', $response->getContent());
    }

    #[Test]
    public function tree_does_not_disclose_an_entry_the_user_may_not_view()
    {
        $this->hiddenEntry();
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'hidden-1'],
        ]);

        $response = $this->actingAs($user)->getJson($this->indexUrl());

        $this->assertBlocked($response);
    }

    #[Test]
    public function tree_keeps_visible_entry_data_next_to_an_entry_the_user_may_not_view()
    {
        $this->visibleEntry();
        $this->hiddenEntry();
        $user = $this->userWith(['view test nav', 'view articles entries']);
        $this->makeNav('test', [
            ['id' => 'visiblepage', 'entry' => 'visible-1'],
            ['id' => 'hiddenpage', 'entry' => 'hidden-1'],
        ]);

        $response = $this->actingAs($user)->getJson($this->indexUrl());

        $response->assertOk();
        $this->assertNotDisclosed($response);
        $this->assertDisclosed($response, ['VISIBLE-TITLE-ABC']);
    }

    #[Test]
    public function saving_the_tree_does_not_disclose_an_entry_the_user_may_not_view()
    {
        $this->hiddenEntry();
        $user = $this->userWith(['edit test nav']);
        $this->makeNav('test', [
            ['id' => 'hiddenpage', 'entry' => 'hidden-1'],
        ]);

        $response = $this->actingAs($user)->patchJson(cp_route('navigation.tree.update', 'test'), [
            'site' => 'en',
            'pages' => [['id' => 'hiddenpage', 'children' => []]],
            'data' => [],
        ]);

        $this->assertBlocked($response);
    }
}
