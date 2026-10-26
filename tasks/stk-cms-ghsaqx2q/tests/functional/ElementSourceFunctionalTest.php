<?php

declare(strict_types=1);

namespace CraftBench\Tests;

use craft\elements\Entry;
use craft\helpers\ElementHelper;
use craft\services\ElementSources;
use CraftBench\Harness;
use PHPUnit\Framework\TestCase;

/**
 * Legitimate source criteria still reach the element index query.
 */
class ElementSourceFunctionalTest extends TestCase
{
    public function testLegitSourceCriteriaStillFilter(): void
    {
        Harness::setElementSources([
            Harness::nativeSource([
                'sectionId' => Harness::$section->id,
            ]),
        ]);

        $source = ElementHelper::findSource(Entry::class, Harness::sourceKey(), ElementSources::CONTEXT_INDEX);
        $this->assertNotNull($source, 'the fixture source was not found');
        $this->assertSame(Harness::$section->id, (int)($source['criteria']['sectionId'] ?? 0));

        [$error, $query] = Harness::elementIndexQuery(Harness::sourceKey());
        $this->assertNull($error, 'the element index query could not be built');
        $this->assertNotNull($query);
        $this->assertSame(Harness::$section->id, (int)$query->sectionId);
    }
}
