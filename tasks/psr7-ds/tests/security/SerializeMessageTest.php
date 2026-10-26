<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use CweBench\Psr7Tests\Support\ForeignRequest;
use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Message;
use PHPUnit\Framework\TestCase;

/**
 * A serialized request must not carry a Host header assembled from a malformed host.
 */
final class SerializeMessageTest extends TestCase
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
    public function testToStringRejectsMalformedUriHost(string $host): void
    {
        $request = new ForeignRequest('GET', new ForeignUri(['scheme' => 'http', 'host' => $host, 'path' => '/']));

        $this->expectException(\InvalidArgumentException::class);

        Message::toString($request);
    }
}
