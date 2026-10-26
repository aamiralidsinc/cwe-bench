<?php

declare(strict_types=1);

namespace CweBench\MongoPhpLibrary\Security;

use MongoDB\Exception\InvalidArgumentException;
use MongoDB\Operation\BulkWrite;
use MongoDB\Operation\Delete;
use MongoDB\Operation\Find;
use MongoDB\Operation\InsertMany;
use MongoDB\Operation\InsertOne;
use MongoDB\Operation\Update;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * The library's operation objects take database and collection names directly and must
 * address exactly those names.
 */
final class OperationNameSecurityTest extends TestCase
{
    /** @return iterable<string, array{string, string, string}> */
    public static function provideInvalidNames(): iterable
    {
        $operations = ['find', 'insertOne', 'insertMany', 'update', 'delete', 'bulkWrite'];
        $names = [
            'period in database name' => ['prod.audit', 'records'],
            'nul byte in database name' => ["prod\0audit", 'records'],
            'nul byte in collection name' => ['prod', "records\0x"],
        ];

        foreach ($operations as $operation) {
            foreach ($names as $shape => [$databaseName, $collectionName]) {
                yield $operation . ', ' . $shape => [$operation, $databaseName, $collectionName];
            }
        }
    }

    #[DataProvider('provideInvalidNames')]
    public function testOperationRefusesInvalidNames(string $operation, string $databaseName, string $collectionName): void
    {
        $this->expectException(InvalidArgumentException::class);

        $this->createOperation($operation, $databaseName, $collectionName);
    }

    private function createOperation(string $operation, string $databaseName, string $collectionName): void
    {
        switch ($operation) {
            case 'find':
                new Find($databaseName, $collectionName, ['marker' => 1]);
                break;
            case 'insertOne':
                new InsertOne($databaseName, $collectionName, ['marker' => 1]);
                break;
            case 'insertMany':
                new InsertMany($databaseName, $collectionName, [['marker' => 1]]);
                break;
            case 'update':
                new Update($databaseName, $collectionName, ['marker' => 1], ['$set' => ['marker' => 2]]);
                break;
            case 'delete':
                new Delete($databaseName, $collectionName, ['marker' => 1], 1);
                break;
            case 'bulkWrite':
                new BulkWrite($databaseName, $collectionName, [
                    [BulkWrite::INSERT_ONE => [['marker' => 1]]],
                ]);
                break;
            default:
                self::fail('unknown operation ' . $operation);
        }
    }
}
