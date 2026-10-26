<?php
declare(strict_types=1);

use PhpOffice\PhpSpreadsheet\Reader\Ods;
use PHPUnit\Framework\TestCase;

final class OdsLegitimateTest extends TestCase
{
    private static function fixture(string $name): string
    {
        return dirname(__DIR__) . '/support/fixtures/' . $name;
    }

    public function testOrdinaryWorkbookLoads(): void
    {
        self::assertTrue((new Ods())->canRead(self::fixture('ordinary.ods')));
        $spreadsheet = (new Ods())->load(self::fixture('ordinary.ods'));
        self::assertSame('Sheet1', $spreadsheet->getSheetNames()[0]);
        self::assertSame('hello', $spreadsheet->getActiveSheet()->getCell('A1')->getValue());
        $spreadsheet->disconnectWorksheets();
    }
}
