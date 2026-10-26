<?php

declare(strict_types=1);

namespace CweBench\EcTrace\Functional;

use CweBench\EcTrace\Fixtures;
use CweBench\EcTrace\WorkTestCase;
use phpseclib3\Crypt\EC;
use phpseclib3\Exception\BadConfigurationException;

/**
 * Legitimate use of X25519 and X448, including the behaviour next to the hardening:
 * standard results, every key form, both curves, and documented engine selection.
 */
final class LegitimateUseTest extends WorkTestCase
{
    public function testX25519PublicKeyVectorsUnderEveryEngine(): void
    {
        foreach ([null, 'PHP', 'libsodium', 'OpenSSL'] as $engine) {
            $this->assertSame(
                Fixtures::X25519_A_PUB,
                $this->withEngine($engine, fn () => $this->deriveRaw(Fixtures::X25519_A_PRIV)),
                'X25519 public key with engine ' . var_export($engine, true)
            );
            $this->assertSame(
                Fixtures::X25519_B_PUB,
                $this->withEngine($engine, fn () => $this->deriveRaw(Fixtures::X25519_B_PRIV)),
                'X25519 public key with engine ' . var_export($engine, true)
            );
        }
    }

    public function testX448PublicKeyVectorsUnderEveryEngine(): void
    {
        foreach ([null, 'PHP', 'OpenSSL'] as $engine) {
            $this->assertSame(
                Fixtures::X448_A_PUB,
                $this->withEngine($engine, fn () => $this->deriveRaw(Fixtures::X448_A_PRIV)),
                'X448 public key with engine ' . var_export($engine, true)
            );
            $this->assertSame(
                Fixtures::X448_B_PUB,
                $this->withEngine($engine, fn () => $this->deriveRaw(Fixtures::X448_B_PRIV)),
                'X448 public key with engine ' . var_export($engine, true)
            );
        }
    }

    public function testEncodedPrivateKeysWithoutAPublicKeyDeriveTheRightPublicKey(): void
    {
        $this->assertSame(Fixtures::X25519_A_PUB, $this->derivePkcs8(Fixtures::PKCS8_X25519_A));
        $this->assertSame(Fixtures::X448_A_PUB, $this->derivePkcs8(Fixtures::PKCS8_X448_A));
        $this->assertSame(
            Fixtures::X448_A_PUB,
            $this->withEngine('PHP', fn () => $this->derivePkcs8(Fixtures::PKCS8_X448_A))
        );
    }

    public function testEncodedPrivateKeysWithAnEmbeddedPublicKeyKeepIt(): void
    {
        $this->assertSame(
            Fixtures::X25519_A_PUB,
            $this->derivePkcs8(Fixtures::PKCS8_X25519_EMBEDDED_ALICE)
        );
        $this->assertSame(
            Fixtures::X448_A_PUB,
            $this->derivePkcs8(Fixtures::PKCS8_X448_EMBEDDED_ALICE)
        );
    }

    public function testSharedSecretVectors(): void
    {
        foreach ([null, 'PHP'] as $engine) {
            $this->assertSame(
                Fixtures::X25519_SHARED,
                $this->withEngine($engine, fn () => $this->sharedSecret(Fixtures::X25519_A_PRIV, Fixtures::X25519_B_PUB))
            );
            $this->assertSame(
                Fixtures::X25519_SHARED,
                $this->withEngine($engine, fn () => $this->sharedSecret(Fixtures::X25519_B_PRIV, Fixtures::X25519_A_PUB))
            );
            $this->assertSame(
                Fixtures::X448_SHARED,
                $this->withEngine($engine, fn () => $this->sharedSecret(Fixtures::X448_A_PRIV, Fixtures::X448_B_PUB))
            );
            $this->assertSame(
                Fixtures::X448_SHARED,
                $this->withEngine($engine, fn () => $this->sharedSecret(Fixtures::X448_B_PRIV, Fixtures::X448_A_PUB))
            );
        }
    }

    public function testGeneratedKeysCanComputeSharedSecrets(): void
    {
        foreach ([null, 'PHP'] as $engine) {
            foreach (['Curve25519' => [32, Fixtures::X25519_B_PUB], 'Curve448' => [56, Fixtures::X448_B_PUB]] as $curve => [$size, $peer]) {
                $key = $this->withEngine($engine, fn () => EC::createKey($curve));
                $this->assertSame($curve, $key->getCurve());
                $this->assertSame($size, strlen($this->scalarBytes($key)), $curve . ' private scalar size');

                $secret = $this->withEngine($engine, fn () => $key->multiply($this->bytes($peer)));
                $this->assertSame($size, strlen($secret), $curve . ' shared-secret size');
                $this->assertNotSame(str_repeat("\0", $size), $secret, $curve . ' shared secret must not be all zero');
            }
        }
    }

    public function testPrivateKeyTextRoundTrip(): void
    {
        foreach ([Fixtures::X25519_A_PRIV, Fixtures::X448_A_PRIV] as $privateHex) {
            $key = EC::loadFormat('MontgomeryPrivate', $this->bytes($privateHex));
            $text = $key->toString('MontgomeryPrivate');
            $reloaded = EC::loadFormat('MontgomeryPrivate', $text);
            $this->assertSame(
                $this->hex($this->publicBytes($key)),
                $this->hex($this->publicBytes($reloaded))
            );
        }
    }

    public function testManyValidKeysKeepLoading(): void
    {
        $seen = [32 => [], 56 => []];
        for ($i = 0; $i < 8; $i++) {
            foreach ([32 => 'Curve25519', 56 => 'Curve448'] as $length => $curve) {
                $key = EC::loadFormat('MontgomeryPrivate', random_bytes($length));
                $this->assertSame($curve, $key->getCurve());
                $seen[$length][$this->hex($this->scalarBytes($key))] = true;
            }
        }
        $this->assertCount(8, $seen[32], 'distinct X25519 private scalars expected');
        $this->assertCount(8, $seen[56], 'distinct X448 private scalars expected');
    }

    public function testDocumentedEngineSelectionStillRejectsUnsupportedCombinations(): void
    {
        $x448 = EC::loadFormat('MontgomeryPrivate', $this->bytes(Fixtures::X448_A_PRIV));
        try {
            $this->withEngine('libsodium', fn () => $x448->multiply($this->bytes(Fixtures::X448_B_PUB)));
            $this->fail('forcing libsodium for X448 shared-secret computation must fail');
        } catch (BadConfigurationException $e) {
            $this->assertNotSame('', $e->getMessage());
        }

        $x25519 = EC::loadFormat('MontgomeryPrivate', $this->bytes(Fixtures::X25519_A_PRIV));
        try {
            $this->withEngine('OpenSSL', fn () => $x25519->multiply($this->bytes(Fixtures::X25519_B_PUB)));
            $this->fail('forcing OpenSSL for shared-secret computation must fail');
        } catch (BadConfigurationException $e) {
            $this->assertNotSame('', $e->getMessage());
        }
    }

    public function testPurePhpEngineWorksWithoutNativeExtensions(): void
    {
        $bootstrap = var_export('/workspace/vendor/autoload.php', true);
        $private = var_export(Fixtures::X448_A_PRIV, true);
        $script = 'require ' . $bootstrap . ';'
            . 'phpseclib3\Crypt\EC::forceEngine("PHP");'
            . '$key = phpseclib3\Crypt\EC::loadFormat("MontgomeryPrivate", hex2bin(' . $private . '));'
            . 'echo bin2hex($key->getPublicKey()->toString("MontgomeryPublic"));';

        $command = escapeshellarg(PHP_BINARY)
            . ' -d disable_functions=sodium_crypto_box_publickey_from_secretkey,'
            . 'sodium_crypto_scalarmult,openssl_pkey_get_private,openssl_pkey_derive'
            . ' -r ' . escapeshellarg($script);

        $output = [];
        $status = 0;
        exec($command, $output, $status);

        $this->assertSame(0, $status, 'the pure-PHP engine must work without native extensions');
        $this->assertSame(Fixtures::X448_A_PUB, implode('', $output));
    }
}
