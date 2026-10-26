<?php

declare(strict_types=1);

namespace CweBench\MongoPhpLibrary\Security;

use MongoDB\Collection;
use MongoDB\Driver\Manager;
use MongoDB\Exception\InvalidArgumentException;
use MongoDB\Operation\RenameCollection;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * A rename has a source namespace and a target namespace; both must address exactly the
 * names the caller supplied.
 */
final class RenameNameSecurityTest extends TestCase
{
    private const URI = 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100';

    private static Manager $manager;

    public static function setUpBeforeClass(): void
    {
        self::$manager = new Manager(self::URI);
    }

    /** @return array<string, array{string, string, string, string}> */
    public static function provideInvalidRenameNames(): array
    {
        return [
            'period in source database name' => ['prod.audit', 'records', 'prod', 'records2'],
            'nul byte in source database name' => ["prod\0audit", 'records', 'prod', 'records2'],
            'nul byte in source collection name' => ['prod', "records\0x", 'prod', 'records2'],
            'period in target database name' => ['prod', 'records', 'prod.audit', 'records2'],
            'leading period in target database name' => ['prod', 'records', '.prod', 'records2'],
            'nul byte in target database name' => ['prod', 'records', "prod\0audit", 'records2'],
            'nul byte in target collection name' => ['prod', 'records', 'prod', "records2\0x"],
        ];
    }

    #[DataProvider('provideInvalidRenameNames')]
    public function testRenameOperationRefusesInvalidNames(
        string $fromDatabaseName,
        string $fromCollectionName,
        string $toDatabaseName,
        string $toCollectionName,
    ): void {
        $this->expectException(InvalidArgumentException::class);

        new RenameCollection($fromDatabaseName, $fromCollectionName, $toDatabaseName, $toCollectionName);
    }

    public function testCollectionRenameRefusesInvalidTargetCollectionName(): void
    {
        $collection = new Collection(self::$manager, 'prod', 'records');

        $this->expectException(InvalidArgumentException::class);
        $collection->rename("records2\0x");
    }

    public function testCollectionRenameRefusesInvalidTargetDatabaseName(): void
    {
        $collection = new Collection(self::$manager, 'prod', 'records');

        $this->expectException(InvalidArgumentException::class);
        $collection->rename('records2', 'prod.audit');
    }
}
