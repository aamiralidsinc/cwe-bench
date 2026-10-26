<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Functional;

use GuzzleHttp\Psr7\Uri;
use PHPUnit\Framework\TestCase;

/**
 * Values that are legitimate hosts keep working exactly as they do today.
 */
final class ValidHostsTest extends TestCase
{
    public static function validHostProvider(): iterable
    {
        yield 'registered name' => ['example.com', 'example.com'];
        yield 'ipv4 address' => ['127.0.0.1', '127.0.0.1'];
        yield 'ipv6 literal' => ['[::1]', '[::1]'];
        yield 'bracket with colons' => ['[a:b]', '[a:b]'];
        yield 'bracket with trailing text' => ['[a]b]', '[a]b]'];
        yield 'empty brackets' => ['[]', '[]'];
        yield 'bracket with non-hex contents' => ['[gggg::1]', '[gggg::1]'];
        yield 'upper case ipv6 literal' => ['[2A00:F48::10]', '[2a00:f48::10]'];
        yield 'zone identifier' => ['[fe80::1%25eth0]', '[fe80::1%25eth0]'];
        yield 'internationalized name' => ["\u{044F}\u{043D}\u{0434}\u{0435}\u{043A}\u{0441}.\u{0440}\u{0444}", "\u{044F}\u{043D}\u{0434}\u{0435}\u{043A}\u{0441}.\u{0440}\u{0444}"];
    }

    /**
     * @dataProvider validHostProvider
     */
    public function testHostSetterKeepsValidHost(string $host, string $expected): void
    {
        $uri = (new Uri())->withHost($host);

        self::assertSame($expected, $uri->getHost());
        self::assertSame($expected, $uri->getAuthority());
    }

    /**
     * @dataProvider validHostProvider
     */
    public function testPartsConstructorKeepsValidHost(string $host, string $expected): void
    {
        $uri = Uri::fromParts(['scheme' => 'http', 'host' => $host]);

        self::assertSame($expected, $uri->getHost());
        self::assertSame($expected, $uri->getAuthority());
    }

    public function testEmptyHostIsStillAccepted(): void
    {
        self::assertSame('', (new Uri())->withHost('')->getHost());
        self::assertSame('', Uri::fromParts(['host' => ''])->getHost());
    }

    public function testBracketedLiteralParsesAsBefore(): void
    {
        $uri = new Uri('http://[2001:db8::1]:8080/path');

        self::assertSame('[2001:db8::1]', $uri->getHost());
        self::assertSame('[2001:db8::1]:8080', $uri->getAuthority());
        self::assertSame(8080, $uri->getPort());
        self::assertSame('http://[2001:db8::1]:8080/path', (string) $uri);
    }
}
