<?php

declare(strict_types=1);

/*
 * Maintenance operations act on stored records without going through the
 * record-command surface. Removing a stored definition that way changes what
 * the site executes just like an ordinary record-command delete does, so it
 * carries the same restriction.
 */

namespace CweTests\Security;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;

final class RecordApiMaintenanceTest extends FunctionalTestCase
{
    #[Test]
    public function permanentlyRemovingADefinitionThroughTheMaintenanceDeleteIsRefused(): void
    {
        $this->actAsFormEditor();
        $before = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($before);
        self::assertSame(0, (int)$before['deleted'], 'fixture row 1 must start out present');

        // The maintenance delete removes a record directly instead of running
        // the record-command map. It must not be able to remove a definition.
        $dataHandler = $this->newDataHandler();
        $dataHandler->start([], []);
        $dataHandler->deleteAction('form_definition', 1, false, true);

        self::assertNotSame([], $dataHandler->errorLog, 'The maintenance delete was not reported as refused.');
        $after = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($after, 'A refused maintenance delete removed the stored definition.');
        self::assertSame(0, (int)$after['deleted'], 'A refused maintenance delete changed the stored state.');
    }
}
