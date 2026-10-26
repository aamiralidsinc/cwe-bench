<?php

/**
 * Legitimate export requests keep working: ordinary folders, folders that do not exist yet,
 * folders reached through a link that stays inside the customer's own tree, and the panel's
 * existing refusal for the folder itself.
 */

declare(strict_types=1);

require_once __DIR__ . '/../harness/FroxlorCase.php';

final class ExportRequestFunctionalTest extends FroxlorCase
{
    public function testOrdinaryNewDestinationIsQueued(): void
    {
        $data = $this->requestExport('/dumpA');

        $this->assertSame($this->docroot() . 'dumpA/', $data['destdir']);
        $this->assertSame(1, $this->queuedRows());
    }

    public function testDestinationThroughLinkInsideFolderIsQueued(): void
    {
        mkdir($this->docroot() . 'releases/v2', 0777, true);
        symlink(rtrim($this->docroot(), '/') . '/releases/v2', rtrim($this->docroot(), '/') . '/current');

        $data = $this->requestExport('/current/dumpB');

        $this->assertNotEmpty($data['destdir']);
        $this->assertDestinationInsideFolder($data['destdir']);
        $this->assertSame(1, $this->queuedRows());
    }

    public function testDestinationCannotBeTheFolderItself(): void
    {
        $this->expectException(\Throwable::class);
        $this->requestExport('/');
    }

    public function testDirectoryNameWithDotsIsAccepted(): void
    {
        $data = $this->requestExport('/backup..2024');

        $this->assertNotEmpty($data['destdir']);
        $this->assertDestinationInsideFolder($data['destdir']);
        $this->assertSame(1, $this->queuedRows());
    }
}
