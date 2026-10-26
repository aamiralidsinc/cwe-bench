<?php

namespace BsBench\Security;

use BsBench\Support;
use PHPUnit\Framework\TestCase;
use Spatie\Browsershot\Browsershot;

/**
 * A caller-supplied base address must not make references inside the document resolve to
 * local files, whether it arrives through its dedicated accessor or as a plain setting.
 */
final class ContentUrlTest extends TestCase
{
    private const DOCUMENT = '<html><body><img src="secret.txt"></body></html>';

    private function assertNotRead(string $directory, array $run, string $marker, string $path): void
    {
        $this->assertStringNotContainsString($marker, $run['body'], 'the output contains the local file');
        $this->assertStringNotContainsString($path, $run['reads'], 'the renderer opened the local file');
        Support::cleanup($directory, dirname($run['output']));
    }

    public function test_local_base_address_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::html(self::DOCUMENT)->setContentUrl('file://'.$dir.'/files/')
        )->save($out));
        $this->assertNotRead($dir, $run, $marker, $path);
    }

    public function test_local_base_address_set_as_a_plain_option_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::html(self::DOCUMENT)->setOption('contentUrl', 'file://'.$dir.'/files/')
        )->save($out));
        $this->assertNotRead($dir, $run, $marker, $path);
    }
}
