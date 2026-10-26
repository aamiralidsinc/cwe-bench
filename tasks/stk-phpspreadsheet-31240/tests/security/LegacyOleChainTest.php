<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

require_once dirname(__DIR__) . '/support/Harness.php';

/**
 * The other container reader the library exposes walks sector chains too; a cyclic chain must
 * terminate with a handled error rather than consuming the process.
 */
final class LegacyOleChainTest extends TestCase
{
    public function testCyclicBlockChainIsRefused(): void
    {
        Harness::assertRefused('ole_read', 'ole_shared_loop.bin');
    }
}
