<?php

/**
 * Work carried out for a customer must not reach outside that customer's folder: not the
 * destination recorded for the job, and not the working directories the job creates beneath it.
 */

declare(strict_types=1);

require_once __DIR__ . '/../harness/FroxlorCase.php';

final class QueuedExportSecurityTest extends FroxlorCase
{
    public function testStoredDestinationOutsideTheFolderIsNotCreatedOrExported(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        $dest = rtrim($this->outsideRoot, '/') . '/stored/';
        $row = $this->queueRow($dest);

        $this->runExportCron($row);

        $this->assertFalse(file_exists($dest), 'the export created a directory outside the customer folder');
        $this->assertOutsideUntouched($before, 'the export changed files outside the customer folder');
    }

    public function testWorkingDirectoryPlantedAsLinkIsNotFollowed(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        $dest = $this->insideDir('dumps');
        symlink(rtrim($this->outsideRoot, '/'), rtrim($dest, '/') . '/.tmp');
        $row = $this->queueRow($dest);

        $this->runExportCron($row);

        $this->assertFileExists($this->preexistingCanary(), 'the export removed files outside the customer folder');
        $this->assertOutsideUntouched($before, 'the export changed files outside the customer folder');
    }

    public function testSubDirectoryPlantedAsLinkIsNotWrittenThrough(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        $dest = $this->insideDir('dumps2');
        mkdir(rtrim($dest, '/') . '/.tmp', 0777, true);
        symlink(rtrim($this->outsideRoot, '/'), rtrim($dest, '/') . '/.tmp/web');
        $row = $this->queueRow($dest);

        $this->runExportCron($row);

        $this->assertOutsideUntouched($before, 'the export wrote outside the customer folder');
    }
}
