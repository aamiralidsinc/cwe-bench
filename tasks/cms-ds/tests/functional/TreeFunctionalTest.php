<?php

namespace Tests\Hidden\Functional;

require_once __DIR__.'/../support/NavTestCase.php';

use PHPUnit\Framework\Attributes\Test;
use Tests\Hidden\NavTestCase;

class TreeFunctionalTest extends NavTestCase
{
    #[Test]
    public function tree_lists_an_entry_page_for_a_user_who_may_view_the_entry()
    {
        $this->visibleEntry();
        $user = $this->userWith(['view test nav', 'view articles entries']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'visible-1'],
        ]);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.tree.index', 'test').'?site=en'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['VISIBLE-TITLE-ABC']);
    }

    #[Test]
    public function tree_lists_a_url_page()
    {
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', [
            ['id' => 'urlpage', 'title' => 'NAV-URL-TITLE', 'url' => '/nav-url'],
        ]);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.tree.index', 'test').'?site=en'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['NAV-URL-TITLE']);
    }

    #[Test]
    public function saving_the_tree_still_returns_the_saved_pages()
    {
        $this->visibleEntry();
        $user = $this->userWith(['edit test nav', 'view articles entries']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'visible-1'],
        ]);

        $response = $this->actingAs($user)->patchJson(cp_route('navigation.tree.update', 'test'), [
            'site' => 'en',
            'pages' => [['id' => 'entrypage', 'children' => []]],
            'data' => [],
        ]);

        $response->assertOk();
        $response->assertJson(['saved' => true]);
        $this->assertDisclosed($response, ['VISIBLE-TITLE-ABC']);
    }
}
