<?php

/**
 * The export request itself must never record a destination that leads out of the customer's
 * own folder, whatever the offending link looks like or where it points.
 */

declare(strict_types=1);

require_once __DIR__ . '/../harness/FroxlorCase.php';

final class ExportRequestSecurityTest extends FroxlorCase
{
    public function testRequestThroughLinkOutOfFolderIsNotQueued(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        symlink(rtrim($this->outsideRoot, '/'), $this->docroot() . 'escape');

        try {
            $this->requestExport('/escape/dump');
        } catch (\Throwable $e) {
            // a refusal is a fine outcome; the assertions below cover the effect either way
        }

        foreach ($this->queuedDestinations() as $destdir) {
            $this->assertDestinationInsideFolder($destdir);
        }
        $this->assertOutsideUntouched($before, 'the request changed files outside the customer folder');
    }

    public function testRequestThroughLinkWithNotYetExistingLeafIsNotQueued(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        symlink(rtrim($this->outsideRoot, '/'), $this->docroot() . 'escape2');

        try {
            $this->requestExport('/escape2/notyet/dump');
        } catch (\Throwable $e) {
            // see above
        }

        foreach ($this->queuedDestinations() as $destdir) {
            $this->assertDestinationInsideFolder($destdir);
        }
        $this->assertOutsideUntouched($before, 'the request changed files outside the customer folder');
    }

    public function testRequestThroughLinkToAnotherFolderIsNotQueued(): void
    {
        // A second customer's folder is outside this customer's own folder just as much as a
        // server directory is.
        $other = $this->caseRoot . '/docroots/test2';
        mkdir($other, 0777, true);
        $before = $this->snapshot($this->outsideRoot);
        symlink($other, $this->docroot() . 'sibling');

        try {
            $this->requestExport('/sibling/dump');
        } catch (\Throwable $e) {
            // see above
        }

        foreach ($this->queuedDestinations() as $destdir) {
            $this->assertDestinationInsideFolder($destdir);
        }
        $this->assertOutsideUntouched($before, 'the request changed files outside the customer folder');
    }

    public function testRequestThroughLinkedLinkIsNotQueued(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        symlink(rtrim($this->outsideRoot, '/'), $this->docroot() . 'hop');
        symlink('hop', $this->docroot() . 'escape3');

        try {
            $this->requestExport('/escape3/dump');
        } catch (\Throwable $e) {
            // see above
        }

        foreach ($this->queuedDestinations() as $destdir) {
            $this->assertDestinationInsideFolder($destdir);
        }
        $this->assertOutsideUntouched($before, 'the request changed files outside the customer folder');
    }
}
