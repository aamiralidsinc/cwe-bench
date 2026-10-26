<?php
declare(strict_types=1);

/**
 * Hidden functional suite: the translation grid keeps filtering per language column.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Functional;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\Translation\Listing as TranslationListing;

/**
 * @internal
 */
final class TranslationFilterFunctionalTest extends Unit
{
    use ProductTrait;

    public function testLanguageColumnStillFilters(): void
    {
        $listing = new TranslationListing();
        $this->applyListingFilters([
            ['key' => 'de', 'type' => 'translationLike', 'filterValue' => 'hello'],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertQualifiedIdentifier($condition, 'de', 'text');
        $this->assertStringContainsString('LIKE', $condition);
        $this->assertContains('%hello%', array_values($listing->getConditionVariables()));
    }
}
