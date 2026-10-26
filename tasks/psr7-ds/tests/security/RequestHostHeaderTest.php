<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Psr7\ServerRequest;
use PHPUnit\Framework\TestCase;

/**
 * A host obtained from another URI implementation must not reach the generated Host header.
 */
final class RequestHostHeaderTest extends TestCase
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

    public static function invalidHostProvider(): iterable
    {
        yield 'user information' => ['vendor.example@evil.example'];
        yield 'path' => ['evil.example/path'];
        yield 'port colon' => ['evil.example:8080'];
        yield 'backslash' => ['evil.example\\path'];
        yield 'opening bracket' => ['[::1'];
    }

    /**
     * @dataProvider invalidHostProvider
     */
    public function testRequestConstructorRejectsMalformedUriHost(string $host): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new Request('GET', new ForeignUri(['host' => $host]));
    }

    /**
     * @dataProvider invalidHostProvider
     */
    public function testRequestUriReplacementRejectsMalformedUriHost(string $host): void
    {
        $this->expectException(\InvalidArgumentException::class);

        (new Request('GET', 'http://good.example/'))
            ->withUri(new ForeignUri(['scheme' => 'https', 'host' => $host]));
    }

    public function testServerNameFallbackRejectsMalformedHost(): void
    {
        $_SERVER = ['HTTP_HOST' => null, 'SERVER_NAME' => 'vendor.example@evil.example'];

        $this->expectException(\InvalidArgumentException::class);

        ServerRequest::getUriFromGlobals();
    }
}
