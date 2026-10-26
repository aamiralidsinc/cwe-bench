<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use GuzzleHttp\Psr7\Message;
use PHPUnit\Framework\TestCase;

/**
 * A request parsed from a message must not record a malformed host.
 */
final class MessageParsingTest extends TestCase
{
    public static function malformedTargetProvider(): iterable
    {
        yield 'unterminated bracket' => ["GET http://[::1/ HTTP/1.1\r\n\r\n"];
        yield 'backslash host' => ["GET http://evil.example\\path/ HTTP/1.1\r\nHost: evil.example\r\n\r\n"];
    }

    /**
     * @dataProvider malformedTargetProvider
     */
    public function testAbsoluteFormTargetRejectsMalformedHost(string $message): void
    {
        $this->expectException(\InvalidArgumentException::class);

        Message::parseRequest($message);
    }
}
