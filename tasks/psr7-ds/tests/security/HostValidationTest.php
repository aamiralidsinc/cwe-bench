<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use GuzzleHttp\Psr7\Uri;
use PHPUnit\Framework\TestCase;

/**
 * A host the library records must be a single well-formed authority host.
 */
final class HostValidationTest extends TestCase
{
    public static function invalidHostProvider(): iterable
    {
        yield 'user information' => ['vendor.example@evil.example'];
        yield 'path' => ['evil.example/path'];
        yield 'query' => ['evil.example?x=1'];
        yield 'fragment' => ['evil.example#frag'];
        yield 'backslash' => ['evil.example\\path'];
        yield 'port colon' => ['evil.example:8080'];
        yield 'opening bracket' => ['[::1'];
        yield 'closing bracket' => ['::1]'];
        yield 'bracket not at the edges' => ['a[::1]'];
        yield 'backslash inside brackets' => ['[a\\b]'];
    }

    /**
     * @dataProvider invalidHostProvider
     */
    public function testHostSetterRejectsMalformedHost(string $host): void
    {
        $this->expectException(\InvalidArgumentException::class);

        (new Uri())->withHost($host);
    }

    /**
     * @dataProvider invalidHostProvider
     */
    public function testPartsConstructorRejectsMalformedHost(string $host): void
    {
        $this->expectException(\InvalidArgumentException::class);

        Uri::fromParts(['scheme' => 'http', 'host' => $host]);
    }

    public static function malformedUriProvider(): iterable
    {
        yield 'backslash host' => ['http://evil.example\\path/'];
        yield 'backslash host no path' => ['http://evil.example\\path'];
        yield 'unterminated bracket' => ['http://[::1/'];
        yield 'scheme-relative bracket host' => ['//[::1]/'];
        yield 'scheme-relative bracket host without path' => ['//[::1]'];
        yield 'user information before bracket host' => ['http://user@[::1]/'];
        yield 'scheme-relative non-hex bracket host' => ['//[gggg::1]/'];
        yield 'bracket host with path delimiter' => ['http://[a/b]/'];
        yield 'bracket host with query delimiter' => ['http://[a?b]/'];
        yield 'bracket host with fragment delimiter' => ['http://[a#b]/'];
        yield 'bracket host with user information delimiter' => ['http://[a@b]/'];
        yield 'backslash inside bracket host' => ['http://[a\\b]/'];
    }

    /**
     * @dataProvider malformedUriProvider
     */
    public function testParsedUriHostAgreesWithAuthority(string $url): void
    {
        try {
            $uri = new Uri($url);
        } catch (\InvalidArgumentException $e) {
            self::assertNotEmpty($e->getMessage());

            return;
        }

        $host = $uri->getHost();
        self::assertDoesNotMatchRegularExpression('~[\x00-\x20\x7F/?#@\\\\]~', $host, 'host carries an authority delimiter');
        if (strpos($host, '[') !== false || strpos($host, ']') !== false) {
            self::assertSame('[', $host[0], 'bracketed host must open with [');
            self::assertSame(']', substr($host, -1), 'bracketed host must close with ]');
        } else {
            self::assertStringNotContainsString(':', $host, 'host carries a port colon');
        }
    }
}
