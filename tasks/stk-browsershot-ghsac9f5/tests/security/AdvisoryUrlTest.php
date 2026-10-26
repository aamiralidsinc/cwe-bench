<?php

namespace BsBench\Security;

use BsBench\Support;
use PHPUnit\Framework\TestCase;
use Spatie\Browsershot\Browsershot;

/**
 * A page address supplied by the caller must not make the renderer open a local file,
 * whichever way that address is written.
 */
final class AdvisoryUrlTest extends TestCase
{
    private static function fileUrl(string $path): string
    {
        return 'file://'.$path;
    }

    private function assertNotRead(string $directory, array $run, string $marker, string $path): void
    {
        $this->assertStringNotContainsString($marker, $run['body'], 'the output contains the local file');
        $this->assertStringNotContainsString($path, $run['reads'], 'the renderer opened the local file');
        Support::cleanup($directory, dirname($run['output']));
    }

    public function test_leading_space_before_a_local_address_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::url('   '.self::fileUrl($path))
        )->save($out));
        $this->assertNotRead($dir, $run, $marker, $path);
    }

    public function test_leading_control_whitespace_before_a_local_address_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::url("\t\n".self::fileUrl($path))
        )->save($out));
        $this->assertNotRead($dir, $run, $marker, $path);
    }

    public function test_source_view_address_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::url('view-source:'.self::fileUrl($path))
        )->save($out));
        $this->assertNotRead($dir, $run, $marker, $path);
    }

    public function test_backslash_local_address_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $written = 'file:\\\\'.str_replace('/', '\\', $path);
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::url($written)
        )->save($out));
        $this->assertNotRead($dir, $run, $marker, $path);
    }
}
