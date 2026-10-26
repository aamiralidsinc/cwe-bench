<?php

namespace Tests\Hidden;

use Facades\Statamic\Fields\BlueprintRepository;
use Facades\Tests\Factories\EntryFactory;
use Statamic\Facades\Blueprint;
use Statamic\Facades\Collection;
use Statamic\Facades\Nav;
use Statamic\Facades\User;
use Tests\FakesRoles;
use Tests\PreventSavingStacheItemsToDisk;
use Tests\TestCase;

abstract class NavTestCase extends TestCase
{
    use FakesRoles;
    use PreventSavingStacheItemsToDisk;

    protected function setUp(): void
    {
        parent::setUp();

        $entryBlueprint = Blueprint::makeFromFields(['foo' => ['type' => 'text']]);
        $navBlueprint = Blueprint::makeFromFields(['foo' => ['type' => 'text']]);

        BlueprintRepository::partialMock();
        BlueprintRepository::shouldReceive('find')->with('navigation.test')->andReturn($navBlueprint);
        BlueprintRepository::shouldReceive('find')->with('navigation.other')->andReturn($navBlueprint);
        BlueprintRepository::shouldReceive('in')->with('collections/articles')->andReturn(collect(['articles' => $entryBlueprint]));
        BlueprintRepository::shouldReceive('in')->with('collections/secrets')->andReturn(collect(['secrets' => $entryBlueprint]));

        Collection::make('articles')->save();
        Collection::make('secrets')->save();
    }

    protected function makeEntry(string $collection, string $id, array $data)
    {
        return EntryFactory::id($id)->collection($collection)->data($data)->create();
    }

    protected function makeNav(string $handle, array $tree, string $site = 'en')
    {
        $nav = tap(Nav::make($handle))->save();
        $nav->makeTree($site, $tree)->save();

        return $nav;
    }

    protected function userWith(array $permissions, ?array $roles = null)
    {
        $this->setTestRoles(['test' => array_merge(['access cp'], $permissions)]);

        return tap(User::make()->assignRole('test'))->save();
    }

    protected function visibleEntry()
    {
        $this->makeEntry('articles', 'visible-1', [
            'title' => 'VISIBLE-TITLE-ABC',
            'foo' => 'VISIBLE-FOO-ABC',
        ]);
    }

    protected function hiddenEntry()
    {
        $this->makeEntry('secrets', 'hidden-1', [
            'title' => 'HIDDEN-TITLE-XYZ',
            'foo' => 'HIDDEN-FOO-XYZ',
            'redirect' => 'HIDDEN-REDIRECT-XYZ',
        ]);
    }

    protected function hiddenMarkers(): array
    {
        return ['HIDDEN-TITLE-XYZ', 'HIDDEN-FOO-XYZ', 'HIDDEN-REDIRECT-XYZ'];
    }

    protected function assertNotDisclosed($response, ?array $markers = null)
    {
        $markers = $markers ?? $this->hiddenMarkers();
        $content = $response->getContent();

        foreach ($markers as $marker) {
            $this->assertStringNotContainsString(
                $marker,
                $content,
                "A hidden entry's value was disclosed while the response was status {$response->status()}"
            );
        }
    }

    /**
     * The attack is blocked when the server refuses with a client error, or answers
     * successfully without the hidden material. A server error is not a refusal.
     */
    protected function assertBlocked($response, ?array $markers = null)
    {
        $markers = $markers ?? $this->hiddenMarkers();

        $this->assertTrue(
            $response->isClientError() || $response->isSuccessful(),
            "Expected a client error or a clean response, got status {$response->status()}"
        );
        $this->assertNotDisclosed($response, $markers);
    }

    protected function assertDisclosed($response, array $markers)
    {
        $content = $response->getContent();

        foreach ($markers as $marker) {
            $this->assertStringContainsString(
                $marker,
                $content,
                "Expected visible value {$marker} in a response with status {$response->status()}"
            );
        }
    }
}
