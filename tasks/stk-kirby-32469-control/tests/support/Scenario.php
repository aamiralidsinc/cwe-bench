<?php

namespace CweBench;

use Kirby\Cms\App;
use Kirby\Cms\Blueprint;
use Kirby\Cms\ModelPermissions;

/**
 * Builds a small Kirby site on disk and drives the real API routes in-process.
 * Values that the tests compare against are computed here with plain PHP.
 */
abstract class Scenario extends \PHPUnit\Framework\TestCase
{
    protected string $root;
    protected string $source;
    protected string $marker;

    protected function setUp(): void
    {
        $this->reset();
        $this->root = sys_get_temp_dir() . '/kbt-' . bin2hex(random_bytes(8));
        mkdir($this->root . '/content/test', 0777, true);
        file_put_contents($this->root . '/content/test/test.txt', "Title: Test\n");

        $this->marker = 'MARKER-' . bin2hex(random_bytes(6));
        $this->source = $this->root . '/payload.md';
        file_put_contents($this->source, $this->marker);
    }

    protected function tearDown(): void
    {
        $this->reset();
        $this->removeTree($this->root);
    }

    protected function reset(): void
    {
        App::destroy();
        Blueprint::$loaded = [];
        ModelPermissions::$cache = [];
    }

    /**
     * Standard roles/users for the scenarios. A role with no `permissions` key is an admin.
     */
    protected function people(): array
    {
        return [
            'roles' => [
                ['name' => 'admin'],
                ['name' => 'no-create', 'permissions' => ['files' => ['create' => false]]],
                ['name' => 'no-replace', 'permissions' => ['files' => ['create' => true, 'replace' => false]]],
                ['name' => 'replace-only', 'permissions' => ['files' => ['create' => false, 'replace' => true]]],
                ['name' => 'no-user-update', 'permissions' => ['user' => ['update' => false], 'users' => ['update' => false]]],
                ['name' => 'self-update-only', 'permissions' => ['user' => ['update' => true], 'users' => ['update' => false]]],
                ['name' => 'users-update-only', 'permissions' => ['user' => ['update' => false], 'users' => ['update' => true]]],
                ['name' => 'no-files', 'permissions' => ['files' => false]],
            ],
            'users' => [
                ['id' => 'admin', 'email' => 'admin@example.com', 'role' => 'admin'],
                ['id' => 'nocreate', 'email' => 'nocreate@example.com', 'role' => 'no-create'],
                ['id' => 'noreplace', 'email' => 'noreplace@example.com', 'role' => 'no-replace'],
                ['id' => 'replaceonly', 'email' => 'replaceonly@example.com', 'role' => 'replace-only'],
                ['id' => 'nouser', 'email' => 'nouser@example.com', 'role' => 'no-user-update'],
                ['id' => 'selfonly', 'email' => 'selfonly@example.com', 'role' => 'self-update-only'],
                ['id' => 'usersonly', 'email' => 'usersonly@example.com', 'role' => 'users-update-only'],
                ['id' => 'nofiles', 'email' => 'nofiles@example.com', 'role' => 'no-files'],
            ],
        ];
    }

    protected function boot(array $props = []): App
    {
        return new App([
            'roots'   => ['index' => $this->root],
            'options' => ['debug' => true, 'api' => ['allowImpersonation' => true]],
            ...$this->people(),
            ...$props,
        ]);
    }

    /**
     * One POST to an API route with one uploaded file. $spec keys: name, body, headers.
     */
    protected function send(App $app, string $path, array $spec = []): \Kirby\Http\Response
    {
        $data = [
            'body'  => $spec['body'] ?? [],
            'files' => [[
                'name'     => $spec['name'] ?? 'payload.md',
                'tmp_name' => $this->source,
                'size'     => (int)filesize($this->source),
                'error'    => 0,
            ]],
        ];

        if (($spec['headers'] ?? null) !== null) {
            $data['headers'] = $spec['headers'];
        }

        return $app->api()->render($path, 'POST', $data);
    }

    /**
     * One request of a multi-request upload.
     */
    protected function chunk(
        App $app,
        string $path,
        string $id,
        int $total,
        int $offset,
        string $content,
        array $body = [],
        string $name = 'payload.md'
    ): \Kirby\Http\Response {
        file_put_contents($this->source, $content);

        return $this->send($app, $path, [
            'name'    => $name,
            'body'    => $body,
            'headers' => [
                'Upload-Length' => $total,
                'Upload-Offset' => $offset,
                'Upload-Id'     => $id,
            ],
        ]);
    }

    /** Filenames present in the upload staging folder. */
    protected function staged(): array
    {
        $dir = $this->root . '/site/cache/.uploads';

        if (is_dir($dir) === false) {
            return [];
        }

        return array_values(array_diff(scandir($dir), ['.', '..']));
    }

    protected function stagedContent(string $name): string|null
    {
        $file = $this->root . '/site/cache/.uploads/' . $name;

        return is_file($file) ? file_get_contents($file) : null;
    }

    /** Paths below the page's content folder. */
    protected function pageFiles(): array
    {
        $dir = $this->root . '/content/test';

        return array_values(array_diff(scandir($dir), ['.', '..']));
    }

    protected function assertClientError(\Kirby\Http\Response $response, string $what = 'request'): void
    {
        $code = $response->code();

        $this->assertGreaterThanOrEqual(400, $code, $what . ' must be refused with a client error, got ' . $code . ': ' . $response->body());
        $this->assertLessThan(500, $code, $what . ' must be a client error, not a server error, got ' . $code . ': ' . $response->body());
    }

    protected function assertNotStored(): void
    {
        $this->assertSame([], $this->staged(), 'no part of the upload may be stored before the request is authorized');
    }

    protected function removeTree(string $path): void
    {
        if (is_dir($path) === false) {
            if (is_file($path)) {
                unlink($path);
            }
            return;
        }

        foreach (array_diff(scandir($path), ['.', '..']) as $entry) {
            $this->removeTree($path . '/' . $entry);
        }

        rmdir($path);
    }
}
