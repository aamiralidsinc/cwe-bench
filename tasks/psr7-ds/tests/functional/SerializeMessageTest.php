<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Functional;

use CweBench\Psr7Tests\Support\ForeignRequest;
use CweBench\Psr7Tests\Support\ForeignUri;
use GuzzleHttp\Psr7\Message;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Psr7\Response;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate messages serialize exactly as they do today.
 */
final class SerializeMessageTest extends TestCase
{
    public function testRequestSerializationKeepsHostHeader(): void
    {
        $message = Message::toString(new Request('GET', 'http://example.com/x?a=b'));

        self::assertStringContainsString("\r\nHost: example.com\r\n", $message);
        self::assertStringStartsWith("GET /x?a=b HTTP/1.1", $message);
    }

    public function testSerializationKeepsExplicitHostHeader(): void
    {
        $message = Message::toString(new Request('GET', 'http://example.com/', ['Host' => 'other.example']));

        self::assertStringContainsString("\r\nHost: other.example\r\n", $message);
    }

    public function testForeignRequestSerializationUsesCallerHostHeader(): void
    {
        $request = new ForeignRequest(
            'GET',
            new ForeignUri(['scheme' => 'https', 'host' => 'example.com', 'path' => '/']),
            ['Host' => 'example.com']
        );

        self::assertStringContainsString("\r\nHost: example.com\r\n", Message::toString($request));
    }

    public function testResponseSerializationIsUnchanged(): void
    {
        $message = Message::toString(new Response(200, ['X-Test' => 'yes'], 'body'));

        self::assertSame("HTTP/1.1 200 OK\r\nX-Test: yes\r\n\r\nbody", $message);
    }
}
