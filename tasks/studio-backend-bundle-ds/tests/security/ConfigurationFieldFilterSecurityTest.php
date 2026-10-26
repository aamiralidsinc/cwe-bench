<?php
declare(strict_types=1);

/**
 * Hidden security suite: the classification-store configuration listings.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Security;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\DataObject\Classificationstore\CollectionConfig\Listing as CollectionConfigListing;
use Pimcore\Model\DataObject\Classificationstore\GroupConfig\Listing as GroupConfigListing;
use Pimcore\Model\DataObject\Classificationstore\KeyConfig\Listing as KeyConfigListing;

/**
 * @internal
 */
final class ConfigurationFieldFilterSecurityTest extends Unit
{
    use ProductTrait;

    public function testQualifiedFieldNameIsNotExecutedOnKeyListing(): void
    {
        $listing = new KeyConfigListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            [
                'key' => 'keys.name=1 OR (SELECT 1) OR keys.name',
                'type' => 'property.filter',
                'filterValue' => 'x',
            ],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testQualifiedFieldNameIsNotExecutedOnGroupListing(): void
    {
        $listing = new GroupConfigListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            [
                'key' => 'groups.name=1 OR (SELECT 1) OR groups.name',
                'type' => 'property.filter',
                'filterValue' => 'x',
            ],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testPlainFieldNameIsNotExecutedOnCollectionListing(): void
    {
        $listing = new CollectionConfigListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            [
                'key' => 'name' . self::IDENTIFIER_ATTACK,
                'type' => 'property.filter',
                'filterValue' => 'x',
            ],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }
}
