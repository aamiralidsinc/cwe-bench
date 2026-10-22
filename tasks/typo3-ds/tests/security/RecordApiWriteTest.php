<?php

declare(strict_types=1);

/*
 * A stored form definition is executable configuration: its finishers and
 * their options decide what happens when a frontend form is submitted. The
 * form editor validates and authorises every saved definition. The generic
 * backend record API must not be able to store a definition that never passed
 * through that path.
 */

namespace CweTests\Security;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;

final class RecordApiWriteTest extends FunctionalTestCase
{
    #[Test]
    public function creatingADefinitionThroughTheRecordApiIsRefused(): void
    {
        $this->actAsFormEditor();

        $dataHandler = $this->newDataHandler();
        $dataHandler->start([
            'form_definition' => [
                'NEW1' => [
                    'pid' => 0,
                    'label' => 'Injected Form',
                    'identifier' => 'cwe-injected-create',
                    'configuration' => $this->attackConfiguration('cwe-injected-create'),
                ],
            ],
        ], []);
        $dataHandler->process_datamap();

        self::assertNotSame([], $dataHandler->errorLog, 'The record write was not reported as refused.');
        self::assertSame(0, $this->countRowsByIdentifier('cwe-injected-create'), 'A refused write stored a new form definition.');
    }

    #[Test]
    public function anAdministrativeRecordWriteOfADefinitionIsRefused(): void
    {
        // The harness is authenticated as an administrator here. The property
        // applies whoever invokes the operation, so this write must be refused
        // just like the same write by a non-administrative user.
        $dataHandler = $this->newDataHandler();
        $dataHandler->start([
            'form_definition' => [
                'NEW1' => [
                    'pid' => 0,
                    'label' => 'Administrative Injected Form',
                    'identifier' => 'cwe-admin-injected',
                    'configuration' => $this->attackConfiguration('cwe-admin-injected'),
                ],
            ],
        ], []);
        $dataHandler->process_datamap();

        self::assertNotSame([], $dataHandler->errorLog, 'The administrative record write was not reported as refused.');
        self::assertSame(0, $this->countRowsByIdentifier('cwe-admin-injected'), 'A refused write stored a new form definition.');
    }

    #[Test]
    public function changingAStoredDefinitionThroughTheRecordApiIsRefused(): void
    {
        $this->actAsFormEditor();
        $before = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($before);

        $dataHandler = $this->newDataHandler();
        $dataHandler->start([
            'form_definition' => [
                1 => [
                    'label' => 'Tampered Label',
                    'identifier' => 'crud-test-form',
                    'configuration' => $this->attackConfiguration('crud-test-form'),
                ],
            ],
        ], []);
        $dataHandler->process_datamap();

        self::assertNotSame([], $dataHandler->errorLog, 'The record write was not reported as refused.');
        $after = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($after);
        self::assertSame($before['configuration'], $after['configuration'], 'A refused write changed the stored configuration.');
        self::assertSame($before['label'], $after['label'], 'A refused write changed the stored label.');
    }

    #[Test]
    public function aPartialRecordUpdateOfADefinitionIsRefused(): void
    {
        $this->actAsFormEditor();
        $before = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($before);

        // A record update that carries no configuration at all still rewrites a
        // stored definition; it must be refused like any other record write.
        $dataHandler = $this->newDataHandler();
        $dataHandler->start(['form_definition' => [1 => ['label' => 'Tampered Label']]], []);
        $dataHandler->process_datamap();

        self::assertNotSame([], $dataHandler->errorLog, 'The partial record write was not reported as refused.');
        $after = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($after);
        self::assertSame($before['label'], $after['label'], 'A refused partial write changed the stored definition.');
    }
}
