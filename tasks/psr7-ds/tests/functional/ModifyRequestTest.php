<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Functional;

use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Psr7\Uri;
use GuzzleHttp\Psr7\Utils;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate URI changes keep producing the same Host header.
 */
final class ModifyRequestTest extends TestCase
{
    public function testUriChangeKeepsHostHeader(): void
    {
        $request = new Request('GET', 'http://foo.example/');
        $modified = Utils::modifyRequest($request, ['uri' => new Uri('http://www.foo.com:8000')]);

        self::assertSame('www.foo.com:8000', $modified->getHeaderLine('Host'));
        self::assertSame('http://www.foo.com:8000', (string) $modified->getUri());
    }

    public function testUriChangeToForeignUriKeepsHostHeader(): void
    {
        $request = new Request('GET', 'http://foo.example/');
        $modified = Utils::modifyRequest($request, [
            'uri' => new ForeignUri(['scheme' => 'https', 'host' => 'example.com', 'port' => 8443, 'path' => '/x']),
        ]);

        self::assertSame('example.com:8443', $modified->getHeaderLine('Host'));
    }

    public function testMissingHostFallsBackToUriHost(): void
    {
        $request = (new Request('GET', 'http://foo.example/path'))->withoutHeader('Host');
        $modified = Utils::modifyRequest($request, ['query' => 'a=b']);

        self::assertSame('foo.example', $modified->getHeaderLine('Host'));
        self::assertSame('a=b', $modified->getUri()->getQuery());
    }

    public function testSetHeadersWithoutUriChangeIsUnaffected(): void
    {
        $request = new Request('GET', 'http://foo.example/');
        $modified = Utils::modifyRequest($request, ['set_headers' => ['X-Test' => '1']]);

        self::assertSame('foo.example', $modified->getHeaderLine('Host'));
        self::assertSame('1', $modified->getHeaderLine('X-Test'));
    }
}
