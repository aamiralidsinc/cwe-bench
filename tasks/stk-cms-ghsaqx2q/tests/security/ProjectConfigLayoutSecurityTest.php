<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use craft\helpers\StringHelper;
use CraftBench\Harness;
use PHPUnit\Framework\TestCase;

/**
 * A layout applied from the project's configuration, rather than from a request.
 */
class ProjectConfigLayoutSecurityTest extends TestCase
{
    private function applyLayout(string $level): void
    {
        $uid = StringHelper::UUID();
        try {
            Harness::setProjectConfig('users.fieldLayouts', [
                $uid => Harness::attackLayout($level, 'as'),
            ]);
        } catch (\Throwable) {
            // The save may fail after the layout has already been built.
        }
    }

    public function testProjectConfigLayoutBehaviorIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        $this->applyLayout('root');
        $this->assertFalse(Harness::markerHit($marker), 'a class named in a configured layout was instantiated');
    }

    public function testProjectConfigTabBehaviorIsNotAttached(): void
    {
        $marker = Harness::newMarker();
        $this->applyLayout('tab');
        $this->assertFalse(Harness::markerHit($marker), 'a class named in a configured layout was instantiated');
    }
}
