<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use CraftBench\Harness;
use PHPUnit\Framework\TestCase;

/**
 * The reported route: a field-layout definition posted to the entry-type settings action.
 */
class PostedLayoutSecurityTest extends TestCase
{
    public function testLayoutLevelBehaviorIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        Harness::postEntryTypeLayout(Harness::attackLayout('root', 'as'));
        $this->assertFalse(Harness::markerHit($marker), 'a class named in the posted layout was instantiated');
    }

    public function testTabLevelBehaviorIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        Harness::postEntryTypeLayout(Harness::attackLayout('tab', 'as'));
        $this->assertFalse(Harness::markerHit($marker), 'a class named in the posted layout was instantiated');
    }

    public function testLayoutLevelEventHandlerIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        Harness::postEntryTypeLayout(Harness::attackLayout('root', 'on'));
        $this->assertFalse(Harness::markerHit($marker), 'an event handler named in the posted layout was invoked');
    }

    public function testTabLevelEventHandlerIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        Harness::postEntryTypeLayout(Harness::attackLayout('tab', 'on'));
        $this->assertFalse(Harness::markerHit($marker), 'an event handler named in the posted layout was invoked');
    }
}
