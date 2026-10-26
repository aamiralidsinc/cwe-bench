<?php
declare(strict_types=1);

/**
 * Hidden security suite: the application-logger listing repository.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Security;

use Codeception\Test\Unit;
use Pimcore\Bundle\StudioBackendBundle\Bundle\ApplicationLogger\Repository\LogRepository;
use Pimcore\Bundle\StudioBackendBundle\Filter\MappedParameter\FilterParameter;
use Pimcore\Bundle\StudioBackendBundle\MappedParameter\CollectionFilterParameter;
use Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support\ProductTrait;

/**
 * @internal
 */
final class ApplicationLoggerFilterSecurityTest extends Unit
{
    use ProductTrait;

    public function testSearchColumnDoesNotExecuteColumnName(): void
    {
        $repository = $this->buildProduct(LogRepository::class);
        $filters = new FilterParameter(columnFilters: [
            ['key' => 'message', 'type' => 'search', 'filterValue' => 'x'],
            ['key' => 'message = 1 OR (SELECT 1) OR message', 'type' => 'search', 'filterValue' => 'x'],
        ]);

        $this->runAllowingRefusal(
            fn () => $repository->list(new CollectionFilterParameter(filters: $filters))
        );

        $this->assertNoRawSql(implode("\n", $this->capturedSql()));
    }

    public function testSearchColumnDoesNotChooseTheParameterName(): void
    {
        $repository = $this->buildProduct(LogRepository::class);
        $filters = new FilterParameter(columnFilters: [
            ['key' => 'message', 'type' => 'search', 'filterValue' => 'x'],
            ['key' => 'message' . self::PARAMETER_ATTACK, 'type' => 'search', 'filterValue' => 'x'],
        ]);

        $this->runAllowingRefusal(
            fn () => $repository->list(new CollectionFilterParameter(filters: $filters))
        );

        $this->assertNoRawSql(implode("\n", $this->capturedSql()));
    }
}
