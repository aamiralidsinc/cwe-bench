<?php

namespace BsBench\Functional;

use PHPUnit\Framework\TestCase;
use Spatie\Browsershot\Browsershot;
use Spatie\Browsershot\Exceptions\FileUrlNotAllowed;
use Spatie\Browsershot\Exceptions\HtmlIsNotAllowedToContainFile;

/**
 * The project's own URL-guard assertions for the affected area, kept unchanged: a plain
 * local address and a local address written in a document are still refused.
 */
final class ProjectUrlGuardTest extends TestCase
{
    public function test_a_file_url_is_refused(): void
    {
        $this->expectException(FileUrlNotAllowed::class);
        Browsershot::url('file://test');
    }

    public function test_a_slightly_malformed_file_url_is_refused(): void
    {
        $this->expectException(FileUrlNotAllowed::class);
        Browsershot::url('file:/test');
    }

    public function test_a_document_containing_a_file_url_is_refused(): void
    {
        $this->expectException(HtmlIsNotAllowedToContainFile::class);
        Browsershot::html('<h1><img src="file://" /></h1>');
    }

    public function test_a_document_containing_a_malformed_file_url_is_refused(): void
    {
        $this->expectException(HtmlIsNotAllowedToContainFile::class);
        Browsershot::html('<h1><img src="file:/" /></h1>');
    }
}
