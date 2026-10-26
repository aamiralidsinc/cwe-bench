<?php

namespace Tests\Hidden\Security;

require_once __DIR__.'/../support/NavTestCase.php';

use PHPUnit\Framework\Attributes\Test;
use Tests\Hidden\NavTestCase;

class PagesSecurityTest extends NavTestCase
{
    private function createUrl(string $nav = 'test', string $query = 'site=en')
    {
        return cp_route('navigation.pages.create', $nav).'?'.$query;
    }

    private function editUrl(string $id, string $nav = 'test', string $query = 'site=en')
    {
        return cp_route('navigation.pages.edit', [$nav, $id]).'?'.$query;
    }

    private function updateUrl(string $nav = 'test')
    {
        return cp_route('navigation.pages.update', $nav);
    }

    #[Test]
    public function create_is_refused_without_permission_to_view_the_navigation()
    {
        $user = $this->userWith([]);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->getJson($this->createUrl());

        $this->assertTrue(
            $response->isClientError(),
            "Expected a client error, got status {$response->status()}"
        );
    }

    #[Test]
    public function edit_is_refused_without_permission_to_view_the_navigation()
    {
        $user = $this->userWith([]);
        $this->makeNav('test', [
            ['id' => 'urlpage', 'title' => 'URL-PAGE-TITLE', 'url' => '/url-page'],
        ]);

        $response = $this->actingAs($user)->getJson($this->editUrl('urlpage'));

        $this->assertTrue(
            $response->isClientError(),
            "Expected a client error, got status {$response->status()}"
        );
    }

    #[Test]
    public function validate_is_refused_without_permission_to_view_the_navigation()
    {
        $user = $this->userWith([]);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->postJson($this->updateUrl(), [
            'site' => 'en',
            'type' => 'url',
            'values' => ['title' => 'A title', 'url' => 'http://example.com'],
        ]);

        $this->assertTrue(
            $response->isClientError(),
            "Expected a client error, got status {$response->status()}"
        );
    }

    #[Test]
    public function create_does_not_disclose_an_entry_the_user_may_not_view()
    {
        $this->hiddenEntry();
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->getJson($this->createUrl(query: 'site=en&entry=hidden-1'));

        $this->assertBlocked($response);
    }

    #[Test]
    public function edit_does_not_disclose_a_stored_entry_the_user_may_not_view()
    {
        $this->hiddenEntry();
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'hidden-1'],
        ]);

        $response = $this->actingAs($user)->getJson($this->editUrl('entrypage'));

        $this->assertBlocked($response);
    }

    #[Test]
    public function edit_is_refused_for_a_site_the_user_may_not_access()
    {
        $this->setSites([
            'en' => ['locale' => 'en', 'url' => '/'],
            'fr' => ['locale' => 'fr', 'url' => '/fr'],
        ]);

        $user = $this->userWith(['view test nav', 'access en site']);
        $nav = $this->makeNav('test', [
            ['id' => 'enpage', 'title' => 'EN-PAGE-MARKER', 'url' => '/en-page'],
        ], 'en');
        $nav->makeTree('fr', [
            ['id' => 'frpage', 'title' => 'FR-PAGE-MARKER', 'url' => '/fr-page'],
        ])->save();

        $response = $this->actingAs($user)->getJson($this->editUrl('frpage', query: 'site=fr'));

        $this->assertTrue(
            $response->isClientError(),
            "Expected a client error, got status {$response->status()}"
        );
        $this->assertStringNotContainsString('FR-PAGE-MARKER', $response->getContent());
    }
}
