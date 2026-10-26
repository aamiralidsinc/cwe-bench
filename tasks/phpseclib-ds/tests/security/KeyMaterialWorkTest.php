<?php

declare(strict_types=1);

namespace CweBench\EcTrace\Security;

use CweBench\EcTrace\Fixtures;
use CweBench\EcTrace\WorkTestCase;
use phpseclib3\Crypt\EC;

/**
 * Deriving a public value from a private scalar must not perform a number of
 * operations that depends on the scalar, whichever engine is selected.
 */
final class KeyMaterialWorkTest extends WorkTestCase
{
    public function testX25519RawKeyWorkIsIndependentOfTheScalar(): void
    {
        $this->assertSame(Fixtures::X25519_A_PUB, $this->deriveRaw(Fixtures::X25519_A_PRIV));
        $this->assertSame(Fixtures::X25519_B_PUB, $this->deriveRaw(Fixtures::X25519_B_PRIV));

        $this->assertSameWork(
            fn () => $this->deriveRaw(Fixtures::X25519_A_PRIV),
            fn () => $this->deriveRaw(Fixtures::X25519_B_PRIV),
            'X25519 public-key derivation'
        );
    }

    public function testX448RawKeyWorkIsIndependentOfTheScalar(): void
    {
        $this->assertSame(Fixtures::X448_A_PUB, $this->deriveRaw(Fixtures::X448_A_PRIV));
        $this->assertSame(Fixtures::X448_B_PUB, $this->deriveRaw(Fixtures::X448_B_PRIV));

        $this->assertSameWork(
            fn () => $this->deriveRaw(Fixtures::X448_A_PRIV),
            fn () => $this->deriveRaw(Fixtures::X448_B_PRIV),
            'X448 public-key derivation'
        );
    }

    public function testX25519RawKeyWorkUnderPurePhpIsIndependentOfTheScalar(): void
    {
        $this->assertSame(
            Fixtures::X25519_A_PUB,
            $this->withEngine('PHP', fn () => $this->deriveRaw(Fixtures::X25519_A_PRIV))
        );

        $this->assertSameWork(
            fn () => $this->withEngine('PHP', fn () => $this->deriveRaw(Fixtures::X25519_A_PRIV)),
            fn () => $this->withEngine('PHP', fn () => $this->deriveRaw(Fixtures::X25519_B_PRIV)),
            'X25519 public-key derivation (pure-PHP engine)'
        );
    }

    public function testX448RawKeyWorkUnderPurePhpIsIndependentOfTheScalar(): void
    {
        $this->assertSame(
            Fixtures::X448_A_PUB,
            $this->withEngine('PHP', fn () => $this->deriveRaw(Fixtures::X448_A_PRIV))
        );

        $this->assertSameWork(
            fn () => $this->withEngine('PHP', fn () => $this->deriveRaw(Fixtures::X448_A_PRIV)),
            fn () => $this->withEngine('PHP', fn () => $this->deriveRaw(Fixtures::X448_B_PRIV)),
            'X448 public-key derivation (pure-PHP engine)'
        );
    }

    public function testPkcs8X448KeyWorkIsIndependentOfTheScalar(): void
    {
        $this->assertSame(Fixtures::X448_A_PUB, $this->derivePkcs8(Fixtures::PKCS8_X448_A));
        $this->assertSame(Fixtures::X448_B_PUB, $this->derivePkcs8(Fixtures::PKCS8_X448_B));

        $this->assertSameWork(
            fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_A),
            fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_B),
            'X448 public-key derivation from an encoded key'
        );
    }

    public function testPkcs8X448KeyWorkUnderPurePhpIsIndependentOfTheScalar(): void
    {
        $this->assertSameWork(
            fn () => $this->withEngine('PHP', fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_A)),
            fn () => $this->withEngine('PHP', fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_B)),
            'X448 public-key derivation from an encoded key (pure-PHP engine)'
        );
    }

    public function testX25519KeyCarryingItsOwnPublicKeyWorkIsIndependentOfTheScalar(): void
    {
        $this->assertSame(
            Fixtures::X25519_EMBEDDED_PUB,
            $this->derivePkcs8(Fixtures::PKCS8_X25519_EMBEDDED_BIG)
        );
        $this->assertSame(
            Fixtures::X25519_EMBEDDED_PUB,
            $this->derivePkcs8(Fixtures::PKCS8_X25519_EMBEDDED_SMALL)
        );

        $this->assertSameWork(
            fn () => $this->derivePkcs8(Fixtures::PKCS8_X25519_EMBEDDED_BIG),
            fn () => $this->derivePkcs8(Fixtures::PKCS8_X25519_EMBEDDED_SMALL),
            'X25519 key carrying its own public key'
        );
    }

    public function testX448KeyCarryingItsOwnPublicKeyWorkIsIndependentOfTheScalar(): void
    {
        $this->assertSame(
            Fixtures::X448_EMBEDDED_PUB,
            $this->derivePkcs8(Fixtures::PKCS8_X448_EMBEDDED_BIG)
        );
        $this->assertSame(
            Fixtures::X448_EMBEDDED_PUB,
            $this->derivePkcs8(Fixtures::PKCS8_X448_EMBEDDED_SMALL)
        );

        $this->assertSameWork(
            fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_EMBEDDED_BIG),
            fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_EMBEDDED_SMALL),
            'X448 key carrying its own public key'
        );
    }
}
