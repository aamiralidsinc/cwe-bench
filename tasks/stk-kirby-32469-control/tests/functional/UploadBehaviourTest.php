<?php

namespace CweBench\Functional;

use CweBench\Scenario;

/**
 * Legitimate uploads keep working, including the values that sit next to each protected route.
 */
class UploadBehaviourTest extends Scenario
{
    private const PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';

    private function storedFile(string $name, string $content): void
    {
        file_put_contents($this->root . '/content/test/' . $name, $content);
    }

    private function avatarSource(string $name = 'avatar.png'): string
    {
        $path = $this->root . '/' . $name;
        file_put_contents($path, base64_decode(self::PNG));

        return $path;
    }

    public function testAuthorizedMultiRequestUploadCompletes(): void
    {
        $app = $this->boot();
        $app->impersonate('admin@example.com');

        $first = $this->chunk($app, 'pages/test/files', 'abcd', 12, 0, 'abcdef');
        $this->assertSame(200, $first->code(), $first->body());

        $second = $this->chunk($app, 'pages/test/files', 'abcd', 12, 6, 'ghijkl');
        $this->assertSame(200, $second->code(), $second->body());

        $this->assertFileExists($this->root . '/content/test/payload.md');
        $this->assertSame('abcdefghijkl', file_get_contents($this->root . '/content/test/payload.md'));
    }

    public function testUploadThatCompletesInItsFirstRequestStillCompletes(): void
    {
        $app = $this->boot();
        $app->impersonate('admin@example.com');

        $response = $this->chunk(
            $app,
            'pages/test/files',
            'abcd',
            strlen($this->marker),
            0,
            $this->marker
        );
        $this->assertSame(200, $response->code(), $response->body());

        $this->assertFileExists($this->root . '/content/test/payload.md');
        $this->assertSame($this->marker, file_get_contents($this->root . '/content/test/payload.md'));
    }

    public function testFieldUploadAllowedByItsDeclaredFileTypeCompletes(): void
    {
        $app = $this->boot([
            'blueprints' => [
                'pages/test' => [
                    'fields' => [
                        'photos' => ['type' => 'files', 'uploads' => ['template' => 'selfservice']],
                    ],
                ],
                'files/selfservice' => ['options' => ['create' => true]],
            ],
        ]);
        // the role denies file creation in general; the declared file type allows it
        $app->impersonate('nocreate@example.com');

        $response = $this->chunk(
            $app,
            'pages/test/fields/photos/upload',
            'abcd',
            strlen($this->marker),
            0,
            $this->marker
        );
        $this->assertSame(200, $response->code(), $response->body());

        $this->assertFileExists($this->root . '/content/test/payload.md');
        $this->assertSame($this->marker, file_get_contents($this->root . '/content/test/payload.md'));
    }

    public function testCallerAllowedOnlyToReplaceCanStillReplace(): void
    {
        $this->storedFile('existing.md', 'ORIGINAL-CONTENT');
        $app = $this->boot();
        // may replace, may not create
        $app->impersonate('replaceonly@example.com');

        $response = $this->chunk(
            $app,
            'pages/test/files/existing.md',
            'abcd',
            strlen($this->marker),
            0,
            $this->marker,
            [],
            'existing.md'
        );
        $this->assertSame(200, $response->code(), $response->body());

        $this->assertSame(
            $this->marker,
            file_get_contents($this->root . '/content/test/existing.md')
        );
    }

    public function testDefaultFileTypeUploadWithoutDeclarationCompletes(): void
    {
        $app = $this->boot();
        $app->impersonate('admin@example.com');

        $response = $this->send($app, 'pages/test/files');
        $this->assertSame(200, $response->code(), $response->body());

        $this->assertFileExists($this->root . '/content/test/payload.md');
        $this->assertSame($this->marker, file_get_contents($this->root . '/content/test/payload.md'));
    }

    public function testSelfServiceAvatarUploadCompletes(): void
    {
        $app = $this->boot();
        $app->impersonate('selfonly@example.com');

        $avatar = $this->avatarSource();
        $this->source = $avatar;
        $content = file_get_contents($avatar);

        $response = $this->chunk(
            $app,
            'account/avatar',
            'abcd',
            strlen($content),
            0,
            $content,
            [],
            'avatar.png'
        );
        $this->assertSame(200, $response->code(), $response->body());
        $this->assertFileExists($this->root . '/site/accounts/selfonly/profile.png');
    }

    public function testAvatarUploadForAnotherAccountWithUsersPermissionCompletes(): void
    {
        $app = $this->boot();
        $app->impersonate('usersonly@example.com');

        $avatar = $this->avatarSource();
        $this->source = $avatar;
        $content = file_get_contents($avatar);

        $response = $this->chunk(
            $app,
            'users/admin/avatar',
            'abcd',
            strlen($content),
            0,
            $content,
            [],
            'avatar.png'
        );
        $this->assertSame(200, $response->code(), $response->body());
        $this->assertFileExists($this->root . '/site/accounts/admin/profile.png');
    }

    public function testUploadHelperCanStillBeUsedWithoutAnAuthorizationHook(): void
    {
        $app = $this->boot();
        $app->impersonate('admin@example.com');

        $api = $app->api()->clone([
            'requestData' => [
                'files' => [[
                    'name'     => 'payload.md',
                    'tmp_name' => $this->source,
                    'size'     => (int)filesize($this->source),
                    'error'    => 0,
                ]],
            ],
        ]);

        $data = $api->upload(
            function (string $source, string $filename) {
                return ['filename' => $filename];
            },
            true,
            true
        );

        $this->assertSame([
            'status' => 'ok',
            'data'   => ['filename' => 'payload.md'],
        ], $data);
    }
}
