<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use craft\elements\Entry;
use craft\helpers\ElementHelper;
use craft\services\ElementSources;
use CraftBench\Harness;
use CraftBench\ProbeBehavior;
use PHPUnit\Framework\TestCase;

/**
 * Element-index source criteria applied to the query the index builds.
 */
class ElementSourceSecurityTest extends TestCase
{
    public function testSourceCriteriaBehaviorIsNotAttached(): void
    {
        $marker = Harness::newMarker();

        Harness::setElementSources([
            Harness::nativeSource([
                'sectionId' => Harness::$section->id,
                'as craftBenchProbe' => ['class' => ProbeBehavior::class],
            ]),
        ]);

        $source = ElementHelper::findSource(Entry::class, Harness::sourceKey(), ElementSources::CONTEXT_INDEX);
        $this->assertNotNull($source, 'the fixture source was not found');

        [$error, $query] = Harness::elementIndexQuery(Harness::sourceKey());

        $this->assertFalse(Harness::markerHit($marker), 'a class named in the source criteria was instantiated');
        if ($query !== null) {
            $this->assertArrayNotHasKey('craftBenchProbe', $query->getBehaviors(),
                'a behavior named in the source criteria was attached');
        }
    }
}
