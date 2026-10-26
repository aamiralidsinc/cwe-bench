<?php
declare(strict_types=1);

/**
 * Hidden functional suite: the note field filters keep their behaviour.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Functional;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Note\MappedParameter\NoteParameters;
use Pimcore\Bundle\StudioBackendBundle\Note\Service\FilterService;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\Element\Note\Listing as NoteListing;

/**
 * @internal
 */
final class NoteFiltersFunctionalTest extends Unit
{
    use ProductTrait;

    public function testNumericFieldStillFilters(): void
    {
        $listing = new NoteListing();
        $filters = json_encode([
            ['field' => 'numeric', 'type' => 'numeric', 'operator' => 'eq', 'value' => 10],
        ], JSON_THROW_ON_ERROR);

        $this->buildProduct(FilterService::class)->applyFieldFilters(
            $listing,
            new NoteParameters(fieldFilters: $filters)
        );

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'numeric');
        $this->assertStringContainsString('=', $condition);
        $this->assertContains(10, array_values($listing->getConditionVariables()));
    }

    public function testDateFieldStillFilters(): void
    {
        $listing = new NoteListing();
        $filters = json_encode([
            ['field' => 'date', 'type' => 'date', 'operator' => 'eq', 'value' => '05/04/2024'],
        ], JSON_THROW_ON_ERROR);

        $this->buildProduct(FilterService::class)->applyFieldFilters(
            $listing,
            new NoteParameters(fieldFilters: $filters)
        );

        $condition = $listing->getCondition();
        $this->assertColumnIdentifier($condition, 'date');
        $this->assertStringContainsString('BETWEEN', $condition);
        $this->assertContains(1714780800, array_values($listing->getConditionVariables()));
        $this->assertContains(1714867199, array_values($listing->getConditionVariables()));
    }

    public function testUserFieldStillFiltersThroughTheUsersTable(): void
    {
        $listing = new NoteListing();
        $filters = json_encode([
            ['field' => 'user', 'type' => 'user', 'operator' => 'user', 'value' => 'admin'],
        ], JSON_THROW_ON_ERROR);

        $this->buildProduct(FilterService::class)->applyFieldFilters(
            $listing,
            new NoteParameters(fieldFilters: $filters)
        );

        $condition = $listing->getCondition();
        $this->assertStringContainsString('users', $condition);
        $this->assertStringContainsString('IN', $condition);
        $this->assertContains('admin', array_values($listing->getConditionVariables()));
    }
}
