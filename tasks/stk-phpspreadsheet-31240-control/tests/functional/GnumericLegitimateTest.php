<?php
declare(strict_types=1);

use PhpOffice\PhpSpreadsheet\Reader\Gnumeric;
use PHPUnit\Framework\TestCase;

final class GnumericLegitimateTest extends TestCase
{
    private static function fixture(string $name): string
    {
        return dirname(__DIR__) . '/support/fixtures/' . $name;
    }

    public function testPlainWorkbookLoads(): void
    {
        self::assertTrue((new Gnumeric())->canRead(self::fixture('plain.gnumeric')));
        $spreadsheet = (new Gnumeric())->load(self::fixture('plain.gnumeric'));
        self::assertSame(['Sheet1'], $spreadsheet->getSheetNames());
        self::assertSame(1, $spreadsheet->getSheetByName('Sheet1')->getCell('A1')->getValue());
        $spreadsheet->disconnectWorksheets();
    }

    public function testCompressedWorkbookOfOrdinarySizeLoads(): void
    {
        self::assertTrue((new Gnumeric())->canRead(self::fixture('large_ok.gnumeric.gz')));
        $spreadsheet = (new Gnumeric())->load(self::fixture('large_ok.gnumeric.gz'));
        self::assertSame(['Sheet1'], $spreadsheet->getSheetNames());
        self::assertGreaterThan(20000, $spreadsheet->getSheetByName('Sheet1')->getHighestRow());
        $spreadsheet->disconnectWorksheets();
    }

    public function testCompressedWorkbookReportsNamesAndInfo(): void
    {
        $reader = new Gnumeric();
        self::assertSame(['Sheet1'], $reader->listWorksheetNames(self::fixture('large_ok.gnumeric.gz')));
        $info = $reader->listWorksheetInfo(self::fixture('large_ok.gnumeric.gz'));
        self::assertSame('Sheet1', $info[0]['worksheetName']);
    }
}
