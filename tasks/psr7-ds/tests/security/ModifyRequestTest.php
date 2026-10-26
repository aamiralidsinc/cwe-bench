<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use CweBench\Psr7Tests\Support\ForeignRequest;
use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Psr7\Utils;
use PHPUnit\Framework\TestCase;

/**
 * A request-modification helper must not copy a malformed host into the Host header.
 */
final class ModifyRequestTest extends TestCase
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
    public function testUriChangeRejectsMalformedHost(string $host): void
    {
        $request = new Request('GET', 'http://good.example/');

        $this->expectException(\InvalidArgumentException::class);

        Utils::modifyRequest($request, ['uri' => new ForeignUri(['scheme' => 'https', 'host' => $host])]);
    }

    public function testMissingHostFallbackRejectsMalformedUriHost(): void
    {
        $request = new ForeignRequest('GET', new ForeignUri(['scheme' => 'http', 'host' => 'evil.example/path']));

        $this->expectException(\InvalidArgumentException::class);

        Utils::modifyRequest($request, ['query' => 'a=b']);
    }
}
