<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

require_once dirname(__DIR__) . '/support/Harness.php';

/**
 * Compressed containers whose entries expand far beyond any ordinary size must be refused before
 * the entry is inflated.
 */
final class ZipEntryBombTest extends TestCase
{
    public function testXlsxLoadRefusesOversizedEntry(): void
    {
        Harness::assertRefused('xlsx_load', 'zipbomb.xlsx');
    }

    public function testOdsLoadRefusesOversizedEntry(): void
    {
        Harness::assertRefused('ods_load', 'zipbomb.ods');
    }
}
