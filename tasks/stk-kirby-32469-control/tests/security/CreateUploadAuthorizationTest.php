<?php

namespace CweBench\Control\Security;

use CweBench\Scenario;

/**
 * The reported upload route must decide that the acting account may create the finished file
 * before any part of the upload is stored.
 */
class CreateUploadAuthorizationTest extends Scenario
{
    public function testCreateRouteDeniesCallerWithoutCreatePermissionBeforeStoring(): void
    {
        $app = $this->boot();
        $app->impersonate('nocreate@example.com');

        $response = $this->chunk($app, 'pages/test/files', 'abcd', 100, 0, $this->marker);

        $this->assertClientError($response, 'create upload');
        $this->assertNotStored();
        $this->assertNotContains('payload.md', $this->pageFiles());
    }

    public function testCreateRouteHonoursDeclaredFileTypePermissionBeforeStoring(): void
    {
        $app = $this->boot([
            'blueprints' => [
                'files/restricted' => ['options' => ['create' => false]],
            ],
        ]);
        $app->impersonate('admin@example.com');

        $response = $this->chunk(
            $app,
            'pages/test/files',
            'abcd',
            100,
            0,
            $this->marker,
            ['template' => 'restricted']
        );

        $this->assertClientError($response, 'create upload for the declared file type');
        $this->assertNotStored();
    }

    public function testCreateRouteDeniesCallerWhoseFileCategoryIsDisabled(): void
    {
        $app = $this->boot();
        $app->impersonate('nofiles@example.com');

        $response = $this->chunk($app, 'pages/test/files', 'abcd', 100, 0, $this->marker);

        $this->assertClientError($response, 'create upload with the file category disabled');
        $this->assertNotStored();
    }

    public function testCreateRouteDeniesUnauthorizedUploadThatCompletesImmediately(): void
    {
        $app = $this->boot();
        $app->impersonate('nocreate@example.com');

        $response = $this->chunk(
            $app,
            'pages/test/files',
            'abcd',
            strlen($this->marker),
            0,
            $this->marker
        );

        $this->assertClientError($response, 'create upload that completes in one request');
        $this->assertNotStored();
        $this->assertNotContains('payload.md', $this->pageFiles());
    }
}
