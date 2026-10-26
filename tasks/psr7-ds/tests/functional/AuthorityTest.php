<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Functional;

use GuzzleHttp\Psr7\Uri;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate authorities keep being split into their components.
 */
final class AuthorityTest extends TestCase
{
    public function testPlainAuthority(): void
    {
        $uri = (new Uri())->withAuthority('example.com');

        self::assertSame('example.com', $uri->getHost());
        self::assertSame('', $uri->getUserInfo());
        self::assertNull($uri->getPort());
        self::assertSame('example.com', $uri->getAuthority());
    }

    public function testAuthorityWithUserInformationAndPort(): void
    {
        $uri = (new Uri())->withAuthority('user:pass@example.com:8080');

        self::assertSame('example.com', $uri->getHost());
        self::assertSame('user:pass', $uri->getUserInfo());
        self::assertSame(8080, $uri->getPort());
        self::assertSame('user:pass@example.com:8080', $uri->getAuthority());
    }

    public function testAuthorityWithBracketedLiteralAndPort(): void
    {
        $uri = (new Uri())->withAuthority('[::1]:8080');

        self::assertSame('[::1]', $uri->getHost());
        self::assertSame(8080, $uri->getPort());
    }

    public function testAuthorityKeepsOtherComponents(): void
    {
        $uri = (new Uri('http://base.example/x'))->withAuthority('other.example');

        self::assertSame('http', $uri->getScheme());
        self::assertSame('other.example', $uri->getHost());
        self::assertSame('/x', $uri->getPath());
        self::assertSame('http://other.example/x', (string) $uri);
    }

    public function testDefaultPortIsRemoved(): void
    {
        $uri = (new Uri('http://base.example/'))->withAuthority('example.com:80');

        self::assertSame('example.com', $uri->getHost());
        self::assertNull($uri->getPort());
        self::assertSame('http://example.com/', (string) $uri);
    }

    public function testEmptyAuthority(): void
    {
        $uri = (new Uri())->withAuthority('');

        self::assertSame('', $uri->getHost());
        self::assertSame('', $uri->getAuthority());
    }
}
