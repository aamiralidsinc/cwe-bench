<?php

declare(strict_types=1);

namespace CweBench\MongoPhpLibrary\Functional;

use MongoDB\Client;
use MongoDB\ClientBulkWrite;
use MongoDB\Collection;
use MongoDB\Database;
use MongoDB\Driver\Manager;
use MongoDB\Exception\InvalidArgumentException;
use MongoDB\GridFS\Bucket;
use MongoDB\Operation\BulkWrite;
use MongoDB\Operation\Delete;
use MongoDB\Operation\Find;
use MongoDB\Operation\InsertMany;
use MongoDB\Operation\InsertOne;
use MongoDB\Operation\RenameCollection;
use MongoDB\Operation\Update;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * Ordinary, legitimate use of the library keeps working.
 */
final class LegitimateUseTest extends TestCase
{
    private const URI = 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100';

    private static Manager $manager;

    public static function setUpBeforeClass(): void
    {
        self::$manager = new Manager(self::URI);
    }

    public function testOrdinaryHandlesKeepTheirNames(): void
    {
        $database = new Database(self::$manager, 'prod');
        self::assertSame('prod', $database->getDatabaseName());

        $collection = new Collection(self::$manager, 'prod', 'records');
        self::assertSame('prod', $collection->getDatabaseName());
        self::assertSame('records', $collection->getCollectionName());
        self::assertSame('prod.records', $collection->getNamespace());
    }

    /** @return array<string, array{string, string}> */
    public static function provideDottedCollectionNames(): array
    {
        return [
            'application dotted name' => ['prod', 'tenant7.orders'],
            'bucket files collection' => ['prod', 'fs.files'],
            'bucket chunks collection' => ['prod', 'fs.chunks'],
            'system collection' => ['prod', 'system.users'],
        ];
    }

    #[DataProvider('provideDottedCollectionNames')]
    public function testCollectionNamesMayContainPeriods(string $databaseName, string $collectionName): void
    {
        $collection = new Collection(self::$manager, $databaseName, $collectionName);

        self::assertSame($databaseName, $collection->getDatabaseName());
        self::assertSame($collectionName, $collection->getCollectionName());
        self::assertSame($databaseName . '.' . $collectionName, $collection->getNamespace());
    }

    public function testGridFSBucketWithDefaultNameConstructs(): void
    {
        $bucket = new Bucket(self::$manager, 'prod');

        self::assertSame('prod', $bucket->getDatabaseName());
        self::assertSame('fs', $bucket->getBucketName());
    }

    public function testGridFSBucketWithDottedNameConstructs(): void
    {
        $bucket = new Bucket(self::$manager, 'prod', ['bucketName' => 'tenant7.files']);

        self::assertSame('prod', $bucket->getDatabaseName());
        self::assertSame('tenant7.files', $bucket->getBucketName());
    }

    /** @return array<string, array{string, string}> */
    public static function provideValidOperationNames(): array
    {
        return [
            'plain' => ['prod', 'records'],
            'dotted collection' => ['prod', 'tenant7.orders'],
            'dashed names' => ['tenant-7', 'audit-log'],
        ];
    }

    #[DataProvider('provideValidOperationNames')]
    public function testOperationsConstructWithValidNames(string $databaseName, string $collectionName): void
    {
        new Find($databaseName, $collectionName, ['marker' => 1]);
        new InsertOne($databaseName, $collectionName, ['marker' => 1]);
        new InsertMany($databaseName, $collectionName, [['marker' => 1]]);
        new Update($databaseName, $collectionName, ['marker' => 1], ['$set' => ['marker' => 2]]);
        new Delete($databaseName, $collectionName, ['marker' => 1], 1);
        new BulkWrite($databaseName, $collectionName, [
            [BulkWrite::INSERT_ONE => [['marker' => 1]]],
        ]);
        new RenameCollection($databaseName, $collectionName, $databaseName, $collectionName . '2');

        self::assertTrue(true);
    }

    public function testRenameToDottedCollectionConstructs(): void
    {
        new RenameCollection('prod', 'records', 'prod', 'tenant7.orders');
        new RenameCollection('prod', 'records', 'other', 'records');

        self::assertTrue(true);
    }

    public function testClientBulkWriteWithValidNamespaceKeepsWorking(): void
    {
        $bulkWrite = ClientBulkWrite::createWithCollection(new Collection(self::$manager, 'prod', 'records'));
        $targeted = $bulkWrite->withNamespace('prod', 'tenant7.orders');

        self::assertNotSame($bulkWrite, $targeted);
        $targeted->insertOne(['marker' => 'writer']);
        self::assertSame(1, $targeted->bulkWriteCommand->count());
    }

    public function testNamespaceFactoryWithPlainNamespaceKeepsWorking(): void
    {
        $collection = Collection::fromNamespace(self::$manager, 'prod.records');

        self::assertSame('prod', $collection->getDatabaseName());
        self::assertSame('records', $collection->getCollectionName());
    }

    public function testEmptyNamesRemainInvalid(): void
    {
        $this->expectException(InvalidArgumentException::class);

        new Database(self::$manager, '');
    }

    public function testEmptyCollectionNameRemainsInvalid(): void
    {
        $this->expectException(InvalidArgumentException::class);

        new Collection(self::$manager, 'prod', '');
    }

    public function testWithOptionsPreservesDottedNames(): void
    {
        $collection = (new Collection(self::$manager, 'prod', 'tenant7.orders'))
            ->withOptions(['typeMap' => ['root' => 'array', 'document' => 'array', 'array' => 'array']]);

        self::assertSame('prod.tenant7.orders', $collection->getNamespace());
    }

    public function testClientHandlesKeepWorking(): void
    {
        $client = new Client(self::URI);

        $database = $client->getDatabase('prod');
        $collection = $database->getCollection('tenant7.orders');

        self::assertSame('prod', $collection->getDatabaseName());
        self::assertSame('tenant7.orders', $collection->getCollectionName());
        self::assertSame('prod.tenant7.orders', $client->getCollection('prod', 'tenant7.orders')->getNamespace());
    }
}
