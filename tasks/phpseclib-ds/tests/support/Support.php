<?php

declare(strict_types=1);

namespace CweBench\EcTrace;

use phpseclib3\Crypt\EC;
use phpseclib3\Crypt\EC\PrivateKey;
use PHPUnit\Framework\TestCase;

final class Fixtures
{
    // RFC 7748 X25519 key pair and shared secret.
    public const X25519_A_PRIV = '77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a';
    public const X25519_A_PUB  = '8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a';
    public const X25519_B_PRIV = '5dab087e624a8a4b79e17f8b83800ee66f3bb1292618b6fd1c2f8b27ff88e0eb';
    public const X25519_B_PUB  = 'de9edb7d7b7dc1b4d35b61c2ece435373f8343c85b78674dadfc7e146f882b4f';
    public const X25519_SHARED = '4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742';

    // RFC 7748 X448 key pair and shared secret.
    public const X448_A_PRIV = '9a8f4925d1519f5775cf46b04b5800d4ee9ee8bae8bc5565d498c28dd9c9baf574a9419744897391006382a6f127ab1d9ac2d8c0a598726b';
    public const X448_A_PUB  = '9b08f7cc31b7e3e67d22d5aea121074a273bd2b83de09c63faa73d2c22c5d9bbc836647241d953d40c5b12da88120d53177f80e532c41fa0';
    public const X448_B_PRIV = '1c306a7ac2a0e2e0990b294470cba339e6453772b075811d8fad0d1d6927c120bb5ee8972b0d3e21374c9c921b09d1b0366f10b65173992d';
    public const X448_B_PUB  = '3eb7a829b0cd20f5bcfc0b599b6feccf6da4627107bdb0d4f345b43027d8b972fc3e34fb4232a13ca706dcb57aec3dae07bdc1c67bf33609';
    public const X448_SHARED = '07fff4181ac6cc95ec1c16a94a0f74d12da232ce40a77552281d282bb60c0b56fd2464c335543936521c24403085d59a449a5037514a879d';

    // Short-magnitude scalars: a valid one followed by zero bytes.
    public const X25519_SMALL_PRIV = '0100000000000000000000000000000000000000000000000000000000000000';
    public const X448_SMALL_PRIV   = '0100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000';

    // PKCS#8 id-X25519 / id-X448 private keys with no embedded public key.
    public const PKCS8_X25519_A = '302e020100300506032b656e0422042077076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a';
    public const PKCS8_X448_A   = '3046020100300506032b656f043a04389a8f4925d1519f5775cf46b04b5800d4ee9ee8bae8bc5565d498c28dd9c9baf574a9419744897391006382a6f127ab1d9ac2d8c0a598726b';
    public const PKCS8_X448_B   = '3046020100300506032b656f043a04381c306a7ac2a0e2e0990b294470cba339e6453772b075811d8fad0d1d6927c120bb5ee8972b0d3e21374c9c921b09d1b0366f10b65173992d';

    // PKCS#8 keys carrying their own public key. BIG and SMALL use the same embedded
    // public value but private scalars of very different magnitude; ALICE carries a
    // consistent RFC 7748 key pair.
    public const X25519_EMBEDDED_PUB = '1111111111111111111111111111111111111111111111111111111111111111';
    public const X448_EMBEDDED_PUB   = '2222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222';

    public const PKCS8_X25519_EMBEDDED_BIG = '3051020101300506032b656e042204207fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8121001111111111111111111111111111111111111111111111111111111111111111';
    public const PKCS8_X25519_EMBEDDED_SMALL = '3051020101300506032b656e0422042001000000000000000000000000000000000000000000000000000000000000008121001111111111111111111111111111111111111111111111111111111111111111';
    public const PKCS8_X448_EMBEDDED_BIG = '308181020101300506032b656f043a04387fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8139002222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222';
    public const PKCS8_X448_EMBEDDED_SMALL = '308181020101300506032b656f043a043801000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008139002222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222';
    public const PKCS8_X25519_EMBEDDED_ALICE = '3051020101300506032b656e0422042077076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a8121008520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a';
    public const PKCS8_X448_EMBEDDED_ALICE = '308181020101300506032b656f043a04389a8f4925d1519f5775cf46b04b5800d4ee9ee8bae8bc5565d498c28dd9c9baf574a9419744897391006382a6f127ab1d9ac2d8c0a598726b8139009b08f7cc31b7e3e67d22d5aea121074a273bd2b83de09c63faa73d2c22c5d9bbc836647241d953d40c5b12da88120d53177f80e532c41fa0';
}

abstract class WorkTestCase extends TestCase
{
    protected function bytes(string $hex): string
    {
        return (string) hex2bin($hex);
    }

    protected function hex(string $bytes): string
    {
        return bin2hex($bytes);
    }

    /**
     * Run both operations and require the same ordered sequence of big-number
     * operations. Values necessarily differ; the work must not.
     */
    protected function assertSameWork(callable $first, callable $second, string $what): void
    {
        $difference = Trace::difference(Trace::ops($first), Trace::ops($second));
        $this->assertNull($difference, $what . ': ' . (string) $difference);
    }

    /**
     * @param non-empty-list<callable> $operations
     */
    protected function assertAllSameWork(array $operations, string $what): void
    {
        $reference = Trace::ops($operations[0]);
        foreach (array_slice($operations, 1) as $index => $operation) {
            $difference = Trace::difference($reference, Trace::ops($operation));
            $this->assertNull($difference, $what . ' (run ' . ($index + 2) . '): ' . (string) $difference);
        }
    }

    /**
     * @param non-empty-list<list<string>> $sequences
     */
    protected function assertSameSequences(array $sequences, string $what): void
    {
        $reference = $sequences[0];
        foreach (array_slice($sequences, 1) as $index => $sequence) {
            $difference = Trace::difference($reference, $sequence);
            $this->assertNull($difference, $what . ' (run ' . ($index + 2) . '): ' . (string) $difference);
        }
    }

    /**
     * @template T
     * @param callable():T $operation
     * @return T
     */
    protected function withEngine(?string $engine, callable $operation)
    {
        EC::forceEngine($engine);
        try {
            return $operation();
        } finally {
            EC::forceEngine(null);
        }
    }

    protected function deriveRaw(string $privateHex): string
    {
        return $this->hex($this->publicBytes(EC::loadFormat('MontgomeryPrivate', $this->bytes($privateHex))));
    }

    protected function derivePkcs8(string $derHex): string
    {
        return $this->hex($this->publicBytes(EC::loadFormat('PKCS8', $this->bytes($derHex))));
    }

    protected function sharedSecret(string $privateHex, string $peerPublicHex): string
    {
        $key = EC::loadFormat('MontgomeryPrivate', $this->bytes($privateHex));
        return $this->hex($key->multiply($this->bytes($peerPublicHex)));
    }

    protected function publicBytes(PrivateKey $key): string
    {
        return $key->getPublicKey()->toString('MontgomeryPublic');
    }

    /** The stored scalar encoding of a private key; stays valid even when a public
     *  coordinate happens to have a leading zero byte. */
    protected function scalarBytes(PrivateKey $key): string
    {
        return $key->toString('MontgomeryPrivate');
    }
}
