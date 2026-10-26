<?php
declare(strict_types=1);

/**
 * Hidden security suite: the translation grid's listing filter.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Security;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\Translation\Listing as TranslationListing;

/**
 * @internal
 */
final class TranslationListingFilterSecurityTest extends Unit
{
    use ProductTrait;

    public function testLanguageKeyIsNotExecuted(): void
    {
        $listing = new TranslationListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            ['key' => 'de) OR (SELECT 1) OR (de', 'type' => 'translationLike', 'filterValue' => 'x'],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testLanguageKeyIsNotUsedInTheParameterName(): void
    {
        $listing = new TranslationListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            ['key' => 'de', 'type' => 'equals', 'filterValue' => 'x'],
            ['key' => 'de' . self::PARAMETER_ATTACK, 'type' => 'translationLike', 'filterValue' => 'x'],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }
}
