<?php
declare(strict_types=1);

/**
 * Hidden functional suite: the application-logger listing keeps working.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Functional;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Bundle\ApplicationLogger\Repository\LogRepository;
use Pimcore\Bundle\StudioBackendBundle\Filter\MappedParameter\FilterParameter;
use Pimcore\Bundle\StudioBackendBundle\MappedParameter\CollectionFilterParameter;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;

/**
 * @internal
 */
final class ApplicationLoggerFunctionalTest extends Unit
{
    use ProductTrait;

    public function testSearchOnARealColumnStillFilters(): void
    {
        $repository = $this->buildProduct(LogRepository::class);
        $filters = new FilterParameter(columnFilters: [
            ['key' => 'message', 'type' => 'search', 'filterValue' => 'database'],
        ]);

        $repository->list(new CollectionFilterParameter(filters: $filters));

        $sql = implode("\n", $this->capturedSql());
        $this->assertStringContainsString('message', $sql);
        $this->assertStringContainsString('LIKE', $sql);
        $this->assertContains('%database%', array_values($this->capturedParameters()[0] ?? []));
    }

    public function testListingWithoutSearchColumnsStillWorks(): void
    {
        $repository = $this->buildProduct(LogRepository::class);

        $repository->list(new CollectionFilterParameter(filters: new FilterParameter()));

        $sql = implode("\n", $this->capturedSql());
        $this->assertStringContainsString('application_logs', $sql);
        $this->assertStringNotContainsString('LIKE', $sql);
    }
}
