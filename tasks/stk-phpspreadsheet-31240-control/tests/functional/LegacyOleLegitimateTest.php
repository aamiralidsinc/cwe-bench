<?php
declare(strict_types=1);

use PhpOffice\PhpSpreadsheet\Shared\OLE;
use PHPUnit\Framework\TestCase;

final class LegacyOleLegitimateTest extends TestCase
{
    private static function fixture(string $name): string
    {
        return dirname(__DIR__) . '/support/fixtures/' . $name;
    }

    public function testOrdinaryContainerStreamsStillRead(): void
    {
        $ole = new OLE();
        $ole->read(self::fixture('pr.4687.excel.xls'));

        self::assertSame(4, $ole->ppsTotal());
        self::assertSame(15712, $ole->getDataLength(1));
        self::assertSame('feff0000', bin2hex($ole->getData(2, 0, 4)));
    }
}
