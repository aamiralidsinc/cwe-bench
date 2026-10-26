<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Functional;

use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Psr7\ServerRequest;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate hosts, including those supplied by another URI implementation, still build the Host header.
 */
final class RequestHostTest extends TestCase
{
    /** @var array<string, mixed> */
    private array $server;

    protected function setUp(): void
    {
        $this->server = $_SERVER;
    }

    protected function tearDown(): void
    {
        $_SERVER = $this->server;
    }

    public static function hostHeaderProvider(): iterable
    {
        yield 'plain host' => [['host' => 'example.com'], 'example.com'];
        yield 'host and port' => [['host' => 'example.com', 'port' => 8080], 'example.com:8080'];
        yield 'ipv6 literal and port' => [['host' => '[::1]', 'port' => 8080], '[::1]:8080'];
    }

    /**
     * @param array<string, mixed> $parts
     *
     * @dataProvider hostHeaderProvider
     */
    public function testConstructorBuildsHostHeader(array $parts, string $expected): void
    {
        $request = new Request('GET', new ForeignUri($parts));

        self::assertSame($expected, $request->getHeaderLine('Host'));
    }

    /**
     * @param array<string, mixed> $parts
     *
     * @dataProvider hostHeaderProvider
     */
    public function testUriReplacementBuildsHostHeader(array $parts, string $expected): void
    {
        $parts['scheme'] = 'https';
        $request = (new Request('GET', 'http://good.example/'))->withUri(new ForeignUri($parts));

        self::assertSame($expected, $request->getHeaderLine('Host'));
    }

    public function testServerNameFallbackKeepsWorking(): void
    {
        $_SERVER = ['HTTP_HOST' => null, 'SERVER_NAME' => 'www.example.org'];

        self::assertSame('www.example.org', ServerRequest::getUriFromGlobals()->getHost());
    }
}
