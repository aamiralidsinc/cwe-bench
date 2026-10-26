<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Functional;

use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Uri;
use GuzzleHttp\Psr7\Utils;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate Host header values keep being formatted the same way.
 */
final class HostHeaderForTest extends TestCase
{
    public function testPlainHost(): void
    {
        self::assertSame('example.com', Utils::hostHeaderFor(new Uri('http://example.com/')));
    }

    public function testHostWithPort(): void
    {
        self::assertSame('example.com:8080', Utils::hostHeaderFor(new Uri('http://example.com:8080/')));
    }

    public function testBracketedLiteralWithPort(): void
    {
        self::assertSame('[::1]:8080', Utils::hostHeaderFor(new Uri('http://[::1]:8080/')));
    }

    public function testEmptyHost(): void
    {
        self::assertSame('', Utils::hostHeaderFor(new Uri('')));
    }

    public function testForeignUri(): void
    {
        self::assertSame('example.com:8443', Utils::hostHeaderFor(
            new ForeignUri(['scheme' => 'https', 'host' => 'example.com', 'port' => 8443])
        ));
    }
}
