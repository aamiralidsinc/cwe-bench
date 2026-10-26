<?php
declare(strict_types=1);

use PhpOffice\PhpSpreadsheet\Reader\Xlsx;
use PHPUnit\Framework\TestCase;

final class XlsxLegitimateTest extends TestCase
{
    private static function fixture(string $name): string
    {
        return dirname(__DIR__) . '/support/fixtures/' . $name;
    }

    public function testOrdinaryWorkbookLoads(): void
    {
        self::assertTrue((new Xlsx())->canRead(self::fixture('ordinary.xlsx')));
        $spreadsheet = (new Xlsx())->load(self::fixture('ordinary.xlsx'));
        self::assertSame('Sheet1', $spreadsheet->getSheetNames()[0]);
        self::assertSame('hello', $spreadsheet->getActiveSheet()->getCell('A1')->getValue());
        $spreadsheet->disconnectWorksheets();
    }

    public function testWorkbookWithLargePartLoads(): void
    {
        $spreadsheet = (new Xlsx())->load(self::fixture('large_sheet.xlsx'));
        self::assertSame('Sheet1', $spreadsheet->getSheetNames()[0]);
        self::assertGreaterThan(10000, $spreadsheet->getActiveSheet()->getHighestRow());
        $spreadsheet->disconnectWorksheets();
    }
}
