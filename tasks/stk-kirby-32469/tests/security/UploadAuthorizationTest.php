<?php

namespace CweBench\Security;

use CweBench\Scenario;

/**
 * Every protected upload route must decide that the acting account may perform the finished
 * operation before any part of the upload is stored.
 */
class UploadAuthorizationTest extends Scenario
{
    private function existingFile(string $name, string $content): void
    {
        file_put_contents($this->root . '/content/test/' . $name, $content);
    }

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
        // the role allows file creation in general; the declared file type does not
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
        $this->assertNotContains('payload.md', $this->pageFiles());
    }

    public function testFieldUploadHonoursItsDeclaredFileTypePermissionBeforeStoring(): void
    {
        $app = $this->boot([
            'blueprints' => [
                'pages/test' => [
                    'fields' => [
                        'photos' => ['type' => 'files', 'uploads' => ['template' => 'restricted']],
                    ],
                ],
                'files/restricted' => ['options' => ['create' => false]],
            ],
        ]);
        $app->impersonate('admin@example.com');

        $response = $this->chunk($app, 'pages/test/fields/photos/upload', 'abcd', 100, 0, $this->marker);

        $this->assertClientError($response, 'field upload');
        $this->assertNotStored();
        $this->assertNotContains('payload.md', $this->pageFiles());
    }

    public function testReplaceRouteDeniesCallerWithoutReplacePermissionBeforeStoring(): void
    {
        $this->existingFile('existing.md', 'ORIGINAL-CONTENT');
        $app = $this->boot();
        $app->impersonate('noreplace@example.com');

        $response = $this->chunk(
            $app,
            'pages/test/files/existing.md',
            'abcd',
            100,
            0,
            $this->marker,
            [],
            'existing.md'
        );

        $this->assertClientError($response, 'replace upload');
        $this->assertNotStored();
        $this->assertSame(
            'ORIGINAL-CONTENT',
            file_get_contents($this->root . '/content/test/existing.md'),
            'the existing file must be untouched'
        );
    }

    public function testAvatarRouteDeniesCallerWithoutPermissionBeforeStoring(): void
    {
        $app = $this->boot();
        $app->impersonate('nouser@example.com');

        $response = $this->chunk($app, 'account/avatar', 'abcd', 100, 0, $this->marker, [], 'avatar.jpg');

        $this->assertClientError($response, 'avatar upload');
        $this->assertNotStored();
    }

    public function testAvatarRouteDeniesChangeToAnotherAccountBeforeStoring(): void
    {
        $app = $this->boot();
        // may update its own account, but not other accounts
        $app->impersonate('selfonly@example.com');

        $response = $this->chunk($app, 'users/admin/avatar', 'abcd', 100, 0, $this->marker, [], 'avatar.jpg');

        $this->assertClientError($response, 'avatar upload for another account');
        $this->assertNotStored();
    }

    public function testUploadDeclarationCannotBeRedeclaredByALaterRequest(): void
    {
        $app = $this->boot([
            'blueprints' => [
                'files/small' => ['accept' => ['maxsize' => 5]],
                'files/large' => ['accept' => ['maxsize' => 500]],
            ],
        ]);
        $app->impersonate('admin@example.com');

        $first = $this->chunk(
            $app,
            'pages/test/files',
            'abcd',
            5,
            0,
            'abc',
            ['template' => 'small']
        );
        $this->assertSame(200, $first->code(), 'an authorized first part must be accepted: ' . $first->body());

        $staged = $this->stagedContent('abcd-payload.md');
        $this->assertSame('abc', $staged, 'the first part must be staged as enough to continue');

        $second = $this->chunk(
            $app,
            'pages/test/files',
            'abcd',
            12,
            3,
            'defghijkl',
            ['template' => 'large']
        );

        $this->assertClientError($second, 're-declared upload');
        $this->assertSame(
            $staged,
            $this->stagedContent('abcd-payload.md'),
            'a refused re-declaration must not append bytes to the staged upload'
        );
        $this->assertNotContains('payload.md', $this->pageFiles());
    }

    public function testForbiddenFilenameIsRejectedBeforeStoringAnyPart(): void
    {
        $app = $this->boot();
        $app->impersonate('admin@example.com');

        $response = $this->chunk($app, 'pages/test/files', 'abcd', 100, 0, $this->marker, [], '.htaccess');

        $this->assertClientError($response, 'upload with a forbidden filename');
        $this->assertNotStored();
        $this->assertNotContains('.htaccess', $this->pageFiles());
    }
}
