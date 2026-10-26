<?php
declare(strict_types=1);

/**
 * Hidden functional suite: the classification-store configuration grid keeps filtering.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Functional;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\DataObject\Classificationstore\KeyConfig\Listing as KeyConfigListing;

/**
 * @internal
 */
final class ConfigurationFieldFilterFunctionalTest extends Unit
{
    use ProductTrait;

    public function testQualifiedFieldStillFilters(): void
    {
        $listing = new KeyConfigListing();
        $this->applyListingFilters([
            ['key' => 'keys.name', 'type' => 'property.filter', 'filterValue' => 'title'],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertQualifiedIdentifier($condition, 'keys', 'name');
        $this->assertStringContainsString('LIKE', $condition);
        $this->assertContains('%title%', array_values($listing->getConditionVariables()));
    }

    public function testPlainFieldStillFilters(): void
    {
        $listing = new KeyConfigListing();
        $this->applyListingFilters([
            ['key' => 'name', 'type' => 'property.filter', 'filterValue' => 'title'],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'name');
        $this->assertStringContainsString('LIKE', $condition);
        $this->assertContains('%title%', array_values($listing->getConditionVariables()));
    }
}
