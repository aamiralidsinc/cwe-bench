<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Utils;
use PHPUnit\Framework\TestCase;

/**
 * A helper that formats a Host header value must not format a malformed host.
 */
final class HostHeaderForTest extends TestCase
{
    public static function invalidHostProvider(): iterable
    {
        yield 'user information' => ['vendor.example@evil.example'];
        yield 'path' => ['evil.example/path'];
        yield 'query' => ['evil.example?x=1'];
        yield 'fragment' => ['evil.example#frag'];

    }

    /**
     * @dataProvider invalidHostProvider
     */
    public function testHostHeaderValueRejectsMalformedHost(string $host): void
    {
        $this->expectException(\InvalidArgumentException::class);

        Utils::hostHeaderFor(new ForeignUri(['scheme' => 'http', 'host' => $host]));
    }
}
