<?php

namespace Tests\Hidden\Functional;

require_once __DIR__.'/../support/NavTestCase.php';

use PHPUnit\Framework\Attributes\Test;
use Tests\Hidden\NavTestCase;

class PagesFunctionalTest extends NavTestCase
{
    #[Test]
    public function create_returns_the_values_of_an_entry_the_user_may_view()
    {
        $this->visibleEntry();
        $user = $this->userWith(['view test nav', 'view articles entries']);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.create', 'test').'?site=en&entry=visible-1'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['VISIBLE-TITLE-ABC', 'VISIBLE-FOO-ABC']);
    }

    #[Test]
    public function create_returns_a_page_for_a_url_item()
    {
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.create', 'test').'?site=en'
        );

        $response->assertOk();
        $response->assertJsonStructure(['values', 'meta', 'localizedFields', 'syncableFields']);
    }

    #[Test]
    public function edit_returns_a_url_page()
    {
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', [
            ['id' => 'urlpage', 'title' => 'URL-PAGE-TITLE', 'url' => '/url-page'],
        ]);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.edit', ['test', 'urlpage']).'?site=en'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['URL-PAGE-TITLE', '/url-page']);
    }

    #[Test]
    public function edit_returns_the_origin_values_of_an_entry_the_user_may_view()
    {
        $this->visibleEntry();
        $user = $this->userWith(['view test nav', 'view articles entries']);
        $this->makeNav('test', [
            ['id' => 'entrypage', 'entry' => 'visible-1'],
        ]);

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.edit', ['test', 'entrypage']).'?site=en'
        );

        $response->assertOk();
        $response->assertJsonStructure(['values', 'originValues', 'originMeta', 'syncableFields']);
        $this->assertDisclosed($response, ['VISIBLE-TITLE-ABC', 'VISIBLE-FOO-ABC']);
    }

    #[Test]
    public function validate_accepts_a_well_formed_page_from_a_viewer()
    {
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->postJson(cp_route('navigation.pages.update', 'test'), [
            'site' => 'en',
            'type' => 'url',
            'values' => ['title' => 'A title', 'url' => 'http://example.com'],
        ]);

        $response->assertOk();
    }

    #[Test]
    public function validate_still_rejects_a_malformed_page_from_a_viewer()
    {
        $user = $this->userWith(['view test nav']);
        $this->makeNav('test', []);

        $response = $this->actingAs($user)->postJson(cp_route('navigation.pages.update', 'test'), [
            'site' => 'en',
            'type' => 'url',
            'values' => [],
        ]);

        $response->assertStatus(422);
    }

    #[Test]
    public function edit_still_works_for_a_site_the_user_may_access()
    {
        $this->setSites([
            'en' => ['locale' => 'en', 'url' => '/'],
            'fr' => ['locale' => 'fr', 'url' => '/fr'],
        ]);

        $user = $this->userWith(['view test nav', 'access en site']);
        $this->makeNav('test', [
            ['id' => 'enpage', 'title' => 'EN-PAGE-MARKER', 'url' => '/en-page'],
        ], 'en');

        $response = $this->actingAs($user)->getJson(
            cp_route('navigation.pages.edit', ['test', 'enpage']).'?site=en'
        );

        $response->assertOk();
        $this->assertDisclosed($response, ['EN-PAGE-MARKER']);
    }
}
