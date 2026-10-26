<?php

declare(strict_types=1);

namespace CweBench\EcTrace\Security;

use CweBench\EcTrace\Fixtures;
use CweBench\EcTrace\Trace;
use CweBench\EcTrace\WorkTestCase;
use phpseclib3\Crypt\EC;

/**
 * Key generation and shared-secret computation also handle a private scalar and must
 * do the same work whatever the scalar's value.
 */
final class SecretOperationWorkTest extends WorkTestCase
{
    public function testCurve448KeyGenerationWorkIsIndependentOfTheScalar(): void
    {
        $sequences = [];
        $publicKeys = [];
        for ($run = 0; $run < 3; $run++) {
            $public = null;
            $sequences[] = Trace::ops(function () use (&$public): void {
                $public = $this->hex($this->scalarBytes(EC::createKey('Curve448')));
            });
            $publicKeys[] = $public;
        }

        $this->assertCount(3, array_unique($publicKeys), 'the runs must use different scalars');
        $this->assertSameSequences($sequences, 'Curve448 key generation');
    }

    public function testCurve25519KeyGenerationWorkUnderPurePhpIsIndependentOfTheScalar(): void
    {
        $sequences = [];
        $publicKeys = [];
        for ($run = 0; $run < 3; $run++) {
            $public = null;
            $sequences[] = Trace::ops(function () use (&$public): void {
                $public = $this->withEngine('PHP', fn () => $this->hex($this->scalarBytes(EC::createKey('Curve25519'))));
            });
            $publicKeys[] = $public;
        }

        $this->assertCount(3, array_unique($publicKeys), 'the runs must use different scalars');
        $this->assertSameSequences($sequences, 'Curve25519 key generation (pure-PHP engine)');
    }

    public function testCurve448SharedSecretWorkIsIndependentOfTheScalar(): void
    {
        $this->assertSame(
            Fixtures::X448_SHARED,
            $this->sharedSecret(Fixtures::X448_A_PRIV, Fixtures::X448_B_PUB)
        );

        $this->assertSameWork(
            fn () => $this->sharedSecret(Fixtures::X448_A_PRIV, Fixtures::X448_B_PUB),
            fn () => $this->sharedSecret(Fixtures::X448_SMALL_PRIV, Fixtures::X448_B_PUB),
            'Curve448 shared-secret computation'
        );
    }

    public function testCurve25519SharedSecretWorkUnderPurePhpIsIndependentOfTheScalar(): void
    {
        $this->assertSame(
            Fixtures::X25519_SHARED,
            $this->withEngine('PHP', fn () => $this->sharedSecret(Fixtures::X25519_A_PRIV, Fixtures::X25519_B_PUB))
        );

        $this->assertSameWork(
            fn () => $this->withEngine('PHP', fn () => $this->sharedSecret(Fixtures::X25519_A_PRIV, Fixtures::X25519_B_PUB)),
            fn () => $this->withEngine('PHP', fn () => $this->sharedSecret(Fixtures::X25519_SMALL_PRIV, Fixtures::X25519_B_PUB)),
            'Curve25519 shared-secret computation (pure-PHP engine)'
        );
    }
}
