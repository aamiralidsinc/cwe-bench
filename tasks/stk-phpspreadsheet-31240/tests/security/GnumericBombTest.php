<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

require_once dirname(__DIR__) . '/support/Harness.php';

/**
 * A compressed workbook that expands far beyond any ordinary size must be refused by every
 * public entry point, not inflated.
 */
final class GnumericBombTest extends TestCase
{
    public function testCanReadRefusesOversizedCompressedFile(): void
    {
        Harness::assertRefused('gnm_canread', 'gzbomb.gnumeric');
    }

    public function testLoadRefusesOversizedCompressedFile(): void
    {
        Harness::assertRefused('gnm_load', 'gzbomb.gnumeric');
    }

    public function testListWorksheetNamesRefusesOversizedCompressedFile(): void
    {
        Harness::assertRefused('gnm_names', 'gzbomb.gnumeric');
    }

    public function testListWorksheetInfoRefusesOversizedCompressedFile(): void
    {
        Harness::assertRefused('gnm_info', 'gzbomb.gnumeric');
    }
}
