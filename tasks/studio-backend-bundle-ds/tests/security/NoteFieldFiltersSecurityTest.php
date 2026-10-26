<?php
declare(strict_types=1);

/**
 * Hidden security suite: the note module's own field filters.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Security;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Note\MappedParameter\NoteParameters;
use Pimcore\Bundle\StudioBackendBundle\Note\Service\FilterService;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;
use Pimcore\Model\Element\Note\Listing as NoteListing;

/**
 * @internal
 */
final class NoteFieldFiltersSecurityTest extends Unit
{
    use ProductTrait;

    public function testFieldNameIsNotExecuted(): void
    {
        $listing = new NoteListing();
        $filters = json_encode([
            [
                'field' => 'date' . self::IDENTIFIER_ATTACK,
                'type' => 'string',
                'operator' => 'eq',
                'value' => 'x',
            ],
        ], JSON_THROW_ON_ERROR);

        $service = $this->buildProduct(FilterService::class);
        $this->runAllowingRefusal(
            fn () => $service->applyFieldFilters($listing, new NoteParameters(fieldFilters: $filters))
        );

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testDateFieldNameIsNotExecuted(): void
    {
        $listing = new NoteListing();
        $filters = json_encode([
            [
                'field' => 'date' . self::IDENTIFIER_ATTACK,
                'type' => 'date',
                'operator' => 'eq',
                'value' => '05/04/2024',
            ],
        ], JSON_THROW_ON_ERROR);

        $service = $this->buildProduct(FilterService::class);
        $this->runAllowingRefusal(
            fn () => $service->applyFieldFilters($listing, new NoteParameters(fieldFilters: $filters))
        );

        $this->assertNoRawSql($listing->getCondition());
    }

    public function testFieldNameDoesNotChooseTheParameterName(): void
    {
        $listing = new NoteListing();
        $filters = json_encode([
            [
                'field' => 'date',
                'type' => 'string',
                'operator' => 'eq',
                'value' => 'x',
            ],
            [
                'field' => 'date' . self::PARAMETER_ATTACK,
                'type' => 'string',
                'operator' => 'eq',
                'value' => 'x',
            ],
        ], JSON_THROW_ON_ERROR);

        $service = $this->buildProduct(FilterService::class);
        $this->runAllowingRefusal(
            fn () => $service->applyFieldFilters($listing, new NoteParameters(fieldFilters: $filters))
        );

        $this->assertNoRawSql($listing->getCondition());
    }
}
