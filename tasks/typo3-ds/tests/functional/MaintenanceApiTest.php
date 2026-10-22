<?php

declare(strict_types=1);

/*
 * Maintenance operations must keep working for ordinary records. Restricting
 * stored form definitions must not make the record layer refuse unrelated
 * tables.
 */

namespace CweTests\Functional;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;
use TYPO3\CMS\Core\Database\ConnectionPool;

final class MaintenanceApiTest extends FunctionalTestCase
{
    #[Test]
    public function permanentlyRemovingAnOrdinaryRecordStillWorks(): void
    {
        $this->importCSVDataSet(dirname(__DIR__) . '/support/Fixtures/tt_content.csv');

        $dataHandler = $this->newDataHandler();
        $dataHandler->start([], []);
        $dataHandler->deleteAction('tt_content', 1, false, true);

        self::assertSame([], $dataHandler->errorLog, 'The ordinary record deletion was refused.');
        $queryBuilder = $this->get(ConnectionPool::class)->getQueryBuilderForTable('tt_content');
        $queryBuilder->getRestrictions()->removeAll();
        $remaining = (int)$queryBuilder
            ->count('uid')
            ->from('tt_content')
            ->where($queryBuilder->expr()->eq('uid', $queryBuilder->createNamedParameter(1)))
            ->executeQuery()
            ->fetchOne();
        self::assertSame(0, $remaining, 'The ordinary record was not removed.');
    }
}
