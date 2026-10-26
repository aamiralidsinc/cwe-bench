<?php
declare(strict_types=1);

/**
 * Hidden functional suite: the shared listing dispatch keeps filtering on real column names.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Functional;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\Element\Note\Listing as NoteListing;

/**
 * @internal
 */
final class ListingFiltersFunctionalTest extends Unit
{
    use ProductTrait;

    public function testDateOnOperatorStillFilters(): void
    {
        $listing = new NoteListing();
        $this->applyListingFilters([
            [
                'key' => 'creationDate',
                'type' => 'date',
                'filterValue' => ['operator' => 'on', 'value' => '2024-06-10'],
            ],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'creationDate');
        $this->assertStringContainsString('BETWEEN', $condition);
        $this->assertContains('2024-06-10 00:00:00', array_values($listing->getConditionVariables()));
        $this->assertContains('2024-06-10 23:59:59', array_values($listing->getConditionVariables()));
    }

    public function testDateRangeOperatorsStillFilter(): void
    {
        foreach ([['from', '2024-06-10 00:00:00'], ['to', '2024-06-10 00:00:00']] as [$operator, $value]) {
            $listing = new NoteListing();
            $this->applyListingFilters([
                [
                    'key' => 'creationDate',
                    'type' => 'date',
                    'filterValue' => ['operator' => $operator, 'value' => '2024-06-10'],
                ],
            ], $listing);

            $condition = $listing->getCondition();
            $this->assertColumnIdentifier($condition, 'creationDate');
            $this->assertMatchesRegularExpression('/[<>]=?/', $condition);
            $this->assertContains($value, array_values($listing->getConditionVariables()));
        }
    }

    public function testEqualsFilterStillFilters(): void
    {
        $listing = new NoteListing();
        $this->applyListingFilters([
            ['key' => 'type', 'type' => 'equals', 'filterValue' => 'asset'],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'type');
        $this->assertStringContainsString('=', $condition);
        $this->assertContains('asset', array_values($listing->getConditionVariables()));
    }

    public function testLikeFilterStillFilters(): void
    {
        $listing = new NoteListing();
        $this->applyListingFilters([
            ['key' => 'filename', 'type' => 'like', 'filterValue' => 'asset'],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'filename');
        $this->assertStringContainsString('LIKE', $condition);
        $this->assertContains('%asset%', array_values($listing->getConditionVariables()));
    }

    public function testMixedCaseColumnStillFilters(): void
    {
        $listing = new NoteListing();
        $this->applyListingFilters([
            ['key' => 'modificationDate', 'type' => 'equals', 'filterValue' => '2024-06-10'],
        ], $listing);

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'modificationDate');
        $this->assertContains('2024-06-10', array_values($listing->getConditionVariables()));
    }
}
