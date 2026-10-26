<?php

namespace BsBench\Security;

use BsBench\Support;
use PHPUnit\Framework\TestCase;
use Spatie\Browsershot\Browsershot;

/**
 * The same rule applies to a page address handed in when the renderer object is built.
 */
final class ConstructorUrlTest extends TestCase
{
    public function test_local_address_given_at_construction_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            new Browsershot('file://'.$path)
        )->save($out));
        try {
            $this->assertStringNotContainsString($marker, $run['body'], 'the output contains the local file');
            $this->assertStringNotContainsString($path, $run['reads'], 'the renderer opened the local file');
        } finally {
            Support::cleanup($dir, dirname($run['output']));
        }
    }

    public function test_source_view_address_given_at_construction_is_refused(): void
    {
        [$dir, $path, $marker] = Support::victim();
        $run = Support::render(fn (string $out) => Support::offline(
            new Browsershot('view-source:file://'.$path)
        )->save($out));
        try {
            $this->assertStringNotContainsString($marker, $run['body'], 'the output contains the local file');
            $this->assertStringNotContainsString($path, $run['reads'], 'the renderer opened the local file');
        } finally {
            Support::cleanup($dir, dirname($run['output']));
        }
    }
}
