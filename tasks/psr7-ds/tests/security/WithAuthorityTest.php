<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Security;

use GuzzleHttp\Psr7\Uri;
use PHPUnit\Framework\TestCase;

/**
 * A host extracted from a supplied authority must be a single well-formed host.
 */
final class WithAuthorityTest extends TestCase
{
    public static function invalidAuthorityProvider(): iterable
    {
        yield 'path' => ['evil.example/path'];
        yield 'query' => ['evil.example?x=1'];
        yield 'fragment' => ['evil.example#frag'];

    }

    /**
     * @dataProvider invalidAuthorityProvider
     */
    public function testAuthoritySetterRejectsMalformedHost(string $authority): void
    {
        $this->expectException(\InvalidArgumentException::class);

        (new Uri())->withAuthority($authority);
    }
}
