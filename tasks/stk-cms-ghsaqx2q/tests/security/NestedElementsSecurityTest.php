<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use CraftBench\Harness;
use PHPUnit\Framework\TestCase;

/**
 * A layout tab whose elements arrive as a JSON string rather than an array: the value is
 * decoded after the outer layout has already been inspected.
 */
class NestedElementsSecurityTest extends TestCase
{
    public function testStringEncodedElementsBehaviorIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        Harness::postEntryTypeLayout(Harness::attackLayout('element', 'as', true));
        $this->assertFalse(Harness::markerHit($marker), 'a class named inside the encoded elements was instantiated');
    }

    public function testStringEncodedElementsHandlerIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        Harness::postEntryTypeLayout(Harness::attackLayout('element', 'on', true));
        $this->assertFalse(Harness::markerHit($marker), 'an event handler named inside the encoded elements was invoked');
    }
}
