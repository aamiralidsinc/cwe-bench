<?php

/**
 * A queued export still runs end to end for a legitimate destination: a folder that does not
 * exist yet, and one reached through a link that stays inside the customer's own tree.
 */

declare(strict_types=1);

require_once __DIR__ . '/../harness/FroxlorCase.php';

final class QueuedExportFunctionalTest extends FroxlorCase
{
    public function testExportToNewFolderStillRuns(): void
    {
        $dest = $this->docroot() . 'exportA/';
        $row = $this->queueRow($dest);

        $this->runExportCron($row);

        $this->assertDirectoryExists(rtrim($dest, '/'), 'the export destination was not created');
        $archives = glob(rtrim($dest, '/') . '/*.tar.gz');
        $this->assertNotEmpty($archives, 'the export archive was not created');
        $this->assertDirectoryDoesNotExist(rtrim($dest, '/') . '/.tmp', 'the export left its working directory behind');
    }

    public function testExportThroughLinkInsideFolderStillRuns(): void
    {
        mkdir($this->docroot() . 'releases/v2', 0777, true);
        symlink(rtrim($this->docroot(), '/') . '/releases/v2', rtrim($this->docroot(), '/') . '/current');
        $this->marker($this->docroot());
        $dest = $this->docroot() . 'current/exportB/';
        $row = $this->queueRow($dest);

        $this->runExportCron($row);

        $this->assertDirectoryExists(rtrim($this->docroot(), '/') . '/releases/v2/exportB', 'the export destination was not created through the in-folder link');
        $archives = glob(rtrim($this->docroot(), '/') . '/releases/v2/exportB/*.tar.gz');
        $this->assertNotEmpty($archives, 'the export archive was not created');
    }
}
