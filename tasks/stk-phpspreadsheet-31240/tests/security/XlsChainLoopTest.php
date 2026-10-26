<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

require_once dirname(__DIR__) . '/support/Harness.php';

/**
 * A workbook whose allocation-table links form a cycle must terminate with a handled error
 * instead of walking the cycle while it grows.
 */
final class XlsChainLoopTest extends TestCase
{
    public function testSsatChainCycleIsRefusedByCanRead(): void
    {
        Harness::assertRefused('xls_canread', 'ole_ssat_loop.xls');
    }

    public function testSsatChainCycleIsRefusedByLoad(): void
    {
        Harness::assertRefused('xls_load', 'ole_ssat_loop.xls');
    }

    public function testDirectoryChainCycleIsRefusedByCanRead(): void
    {
        Harness::assertRefused('xls_canread', 'ole_dir_loop.xls');
    }

    public function testDirectoryChainCycleIsRefusedByLoad(): void
    {
        Harness::assertRefused('xls_load', 'ole_dir_loop.xls');
    }

    public function testSmallStreamChainCycleIsRefusedByLoad(): void
    {
        Harness::assertRefused('xls_load', 'ole_small_loop.xls');
    }

    public function testBigStreamChainCycleIsRefusedByLoad(): void
    {
        Harness::assertRefused('xls_load', 'ole_big_loop.xls');
    }

    public function testSmallStreamChainCycleIsRefusedByListWorksheetNames(): void
    {
        Harness::assertRefused('xls_names', 'ole_small_loop.xls');
    }
}
