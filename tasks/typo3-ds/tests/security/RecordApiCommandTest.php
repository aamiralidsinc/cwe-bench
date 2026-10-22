<?php

declare(strict_types=1);

/*
 * Removing, re-activating or duplicating a stored definition changes what the
 * site executes, exactly like storing one does. The generic record API's
 * command operations therefore carry the same restriction as its write
 * operations.
 */

namespace CweTests\Security;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;
use TYPO3\CMS\Core\Database\ConnectionPool;

final class RecordApiCommandTest extends FunctionalTestCase
{
    /**
     * Number of rows in the storage table, including soft-deleted ones, read
     * without going through any product repository that a fix may harden.
     */
    private function countAllRows(): int
    {
        $queryBuilder = $this->get(ConnectionPool::class)->getQueryBuilderForTable('form_definition');
        $queryBuilder->getRestrictions()->removeAll();
        return (int)$queryBuilder
            ->count('uid')
            ->from('form_definition')
            ->executeQuery()
            ->fetchOne();
    }

    #[Test]
    public function deletingADefinitionThroughTheRecordApiIsRefused(): void
    {
        $this->actAsFormEditor();
        $before = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($before);

        $dataHandler = $this->newDataHandler();
        $dataHandler->start([], ['form_definition' => [1 => ['delete' => 1]]]);
        $dataHandler->process_cmdmap();

        self::assertNotSame([], $dataHandler->errorLog, 'The record command was not reported as refused.');
        $after = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($after);
        self::assertSame((int)$before['deleted'], (int)$after['deleted'], 'A refused command removed the stored definition.');
    }

    #[Test]
    public function reActivatingADefinitionThroughTheRecordApiIsRefused(): void
    {
        $this->actAsFormEditor();
        $before = $this->fetchRowIncludingDeleted(2);
        self::assertIsArray($before);
        self::assertSame(1, (int)$before['deleted'], 'fixture row 2 must start out removed');

        $dataHandler = $this->newDataHandler();
        $dataHandler->start([], ['form_definition' => [2 => ['undelete' => 1]]]);
        $dataHandler->process_cmdmap();

        self::assertNotSame([], $dataHandler->errorLog, 'The record command was not reported as refused.');
        $after = $this->fetchRowIncludingDeleted(2);
        self::assertIsArray($after);
        self::assertSame(1, (int)$after['deleted'], 'A refused command re-activated the stored definition.');
    }

    #[Test]
    public function copyingADefinitionThroughTheRecordCommandIsRefused(): void
    {
        $this->actAsFormEditor();
        $before = $this->countAllRows();
        self::assertSame(3, $before, 'fixture must start with three stored definitions');

        // A copy operation stores a second, independently listed definition
        // without going through the form framework's persistence path.
        $dataHandler = $this->newDataHandler();
        $dataHandler->start([], ['form_definition' => [1 => ['copy' => 0]]]);
        $dataHandler->process_cmdmap();

        self::assertNotSame([], $dataHandler->errorLog, 'The record command was not reported as refused.');
        self::assertSame($before, $this->countAllRows(), 'A refused copy stored another form definition.');
    }
}
