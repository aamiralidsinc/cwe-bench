<?php
declare(strict_types=1);

use PhpOffice\PhpSpreadsheet\Reader\Xls;
use PhpOffice\PhpSpreadsheet\Shared\OLERead;
use PHPUnit\Framework\TestCase;

final class XlsLegitimateTest extends TestCase
{
    private static function fixture(string $name): string
    {
        return dirname(__DIR__) . '/support/fixtures/' . $name;
    }

    public function testOrdinaryWorkbookLoads(): void
    {
        self::assertTrue((new Xls())->canRead(self::fixture('sample.xls')));
        $spreadsheet = (new Xls())->load(self::fixture('sample.xls'));
        self::assertNotEmpty($spreadsheet->getSheetNames());
        $spreadsheet->disconnectWorksheets();
    }

    public function testWorkbookWithSummaryStreamsLoads(): void
    {
        $spreadsheet = (new Xls())->load(self::fixture('CF_Basic_Comparisons.xls'));
        self::assertNotEmpty($spreadsheet->getSheetNames());
        $spreadsheet->disconnectWorksheets();
    }

    /**
     * One container is read once and several of its streams are extracted from the same
     * instance, which is how a workbook and its summary streams are used.
     */
    public function testSeveralStreamsFromOneContainerInstance(): void
    {
        $ole = new OLERead();
        $ole->read(self::fixture('CF_Basic_Comparisons.xls'));

        self::assertNotNull($ole->wrkbook);
        self::assertNotNull($ole->summaryInformation);
        self::assertNotNull($ole->documentSummaryInformation);

        $workbook = $ole->getStream($ole->wrkbook);
        $summary = $ole->getStream($ole->summaryInformation);
        $document = $ole->getStream($ole->documentSummaryInformation);

        self::assertSame(6144, strlen((string) $workbook));
        self::assertSame(448, strlen((string) $summary));
        self::assertSame(320, strlen((string) $document));
        self::assertSame('0908', bin2hex(substr((string) $workbook, 0, 2)));
    }

    public function testWorkbookCanBeReadAgainFromANewInstance(): void
    {
        $first = new OLERead();
        $first->read(self::fixture('CF_Basic_Comparisons.xls'));
        self::assertNotEmpty((string) $first->getStream($first->wrkbook));

        $second = new OLERead();
        $second->read(self::fixture('CF_Basic_Comparisons.xls'));
        self::assertSame($first->getStream($first->wrkbook), $second->getStream($second->wrkbook));
    }
}
