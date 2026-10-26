<?php
declare(strict_types=1);

/**
 * Hidden security suite: the shared listing dispatch used by the collection endpoints.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Security;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\Element\Note\Listing as NoteListing;

/**
 * @internal
 */
final class ListingFiltersSecurityTest extends Unit
{
    use ProductTrait;

    public function testDateRangeFilterDoesNotExecuteColumnName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            [
                'key' => 'creationDate' . self::IDENTIFIER_ATTACK,
                'type' => 'date',
                'filterValue' => ['operator' => 'from', 'value' => '2024-01-01'],
            ],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testDateOnFilterDoesNotExecuteColumnName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            [
                'key' => 'creationDate' . self::IDENTIFIER_ATTACK,
                'type' => 'date',
                'filterValue' => ['operator' => 'on', 'value' => '2024-01-01'],
            ],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testEqualsFilterDoesNotExecuteColumnName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            ['key' => 'type' . self::IDENTIFIER_ATTACK, 'type' => 'equals', 'filterValue' => 'asset'],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testLikeFilterDoesNotExecuteColumnName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            ['key' => 'filename' . self::IDENTIFIER_ATTACK, 'type' => 'like', 'filterValue' => 'asset'],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testDateColumnNameDoesNotChooseTheParameterName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            [
                'key' => 'creationDate',
                'type' => 'date',
                'filterValue' => ['operator' => 'from', 'value' => '2024-01-01'],
            ],
            [
                'key' => 'creationDate' . self::PARAMETER_ATTACK,
                'type' => 'date',
                'filterValue' => ['operator' => 'from', 'value' => '2024-01-01'],
            ],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testEqualsColumnNameDoesNotChooseTheParameterName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            ['key' => 'type', 'type' => 'equals', 'filterValue' => 'asset'],
            ['key' => 'type' . self::PARAMETER_ATTACK, 'type' => 'equals', 'filterValue' => 'asset'],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testLikeColumnNameDoesNotChooseTheParameterName(): void
    {
        $listing = new NoteListing();

        $this->runAllowingRefusal(fn () => $this->applyListingFilters([
            ['key' => 'filename', 'type' => 'like', 'filterValue' => 'asset'],
            ['key' => 'filename' . self::PARAMETER_ATTACK, 'type' => 'like', 'filterValue' => 'asset'],
        ], $listing));

        $this->assertNoRawSql($listing->getCondition());
    }
}
