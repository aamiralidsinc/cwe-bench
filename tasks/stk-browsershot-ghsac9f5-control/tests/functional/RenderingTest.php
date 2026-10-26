<?php

namespace BsBench\Functional;

use BsBench\Support;
use PHPUnit\Framework\TestCase;
use Spatie\Browsershot\Browsershot;

/**
 * Legitimate rendering keeps working: remote pages, documents supplied as text, documents
 * supplied as a local file, and a remote base address for relative references.
 */
final class RenderingTest extends TestCase
{
    public function test_remote_page_renders(): void
    {
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::url('https://example.com/page')
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString('REMOTE-OK', $run['body']);
        } finally {
            Support::cleanup(dirname($run['output']));
        }
    }

    public function test_remote_page_given_at_construction_renders(): void
    {
        $run = Support::render(fn (string $out) => Support::offline(
            new Browsershot('https://example.com/page')
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString('REMOTE-OK', $run['body']);
        } finally {
            Support::cleanup(dirname($run['output']));
        }
    }

    public function test_page_surrounded_by_whitespace_renders(): void
    {
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::url("  https://example.com/page \n")
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString('REMOTE-OK', $run['body']);
        } finally {
            Support::cleanup(dirname($run['output']));
        }
    }

    public function test_document_supplied_as_text_renders(): void
    {
        $html = '<html><body><h1>Hello</h1></body></html>';
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::html($html)
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString($html, $run['body']);
        } finally {
            Support::cleanup(dirname($run['output']));
        }
    }

    public function test_document_supplied_as_a_local_file_renders(): void
    {
        $html = '<html><body><h1>From a file</h1></body></html>';
        $file = Support::htmlFile($html);
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::htmlFromFilePath($file)
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString($html, $run['body']);
        } finally {
            Support::cleanup(dirname($file), dirname($run['output']));
        }
    }

    public function test_remote_base_address_keeps_relative_references_working(): void
    {
        $html = '<html><body><img src="logo.png"></body></html>';
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::html($html)->setContentUrl('https://example.com/assets/')
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString('<img src="logo.png">', $run['body']);
        } finally {
            Support::cleanup(dirname($run['output']));
        }
    }

    public function test_remote_base_address_set_as_a_plain_option_keeps_relative_references_working(): void
    {
        $html = '<html><body><img src="logo.png"></body></html>';
        $run = Support::render(fn (string $out) => Support::offline(
            Browsershot::html($html)->setOption('contentUrl', 'https://example.com/assets/')
        )->save($out));
        try {
            $this->assertFileExists($run['output']);
            $this->assertStringContainsString('<img src="logo.png">', $run['body']);
        } finally {
            Support::cleanup(dirname($run['output']));
        }
    }
}
