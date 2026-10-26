<?php

declare(strict_types=1);

namespace CweBench\MongoPhpLibrary\Security;

use MongoDB\Client;
use MongoDB\Collection;
use MongoDB\Database;
use MongoDB\Driver\Manager;
use MongoDB\Exception\InvalidArgumentException;
use MongoDB\GridFS\Bucket;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * A database or collection handle must address exactly the names it was given.
 */
final class HandleNameSecurityTest extends TestCase
{
    private const URI = 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100';

    private static Manager $manager;

    public static function setUpBeforeClass(): void
    {
        self::$manager = new Manager(self::URI);
    }

    /** @return array<string, array{string}> */
    public static function provideInvalidDatabaseNames(): array
    {
        return [
            'period' => ['prod.audit'],
            'leading period' => ['.prod'],
            'trailing period' => ['prod.'],
            'several periods' => ['prod.audit.archive'],
            'nul byte' => ["prod\0audit"],
        ];
    }

    /** @return array<string, array{string}> */
    public static function provideInvalidCollectionNames(): array
    {
        return [
            'nul byte' => ["records\0x"],
            'trailing nul byte' => ["records\0"],
        ];
    }

    #[DataProvider('provideInvalidDatabaseNames')]
    public function testDatabaseHandleRefusesInvalidDatabaseName(string $databaseName): void
    {
        $this->expectException(InvalidArgumentException::class);

        new Database(self::$manager, $databaseName);
    }

    #[DataProvider('provideInvalidDatabaseNames')]
    public function testCollectionHandleRefusesInvalidDatabaseName(string $databaseName): void
    {
        $this->expectException(InvalidArgumentException::class);

        new Collection(self::$manager, $databaseName, 'records');
    }

    #[DataProvider('provideInvalidCollectionNames')]
    public function testCollectionHandleRefusesInvalidCollectionName(string $collectionName): void
    {
        $this->expectException(InvalidArgumentException::class);

        new Collection(self::$manager, 'prod', $collectionName);
    }

    public function testClientGetDatabaseRefusesInvalidName(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->getDatabase('prod.audit');
    }

    public function testClientGetCollectionRefusesInvalidDatabaseName(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->getCollection('prod.audit', 'records');
    }

    public function testClientGetCollectionRefusesInvalidCollectionName(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->getCollection('prod', "records\0x");
    }

    public function testClientSelectCollectionRefusesInvalidNames(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->selectCollection("prod\0audit", 'records');
    }

    public function testDatabaseGetCollectionRefusesInvalidCollectionName(): void
    {
        $database = new Database(self::$manager, 'prod');

        $this->expectException(InvalidArgumentException::class);
        $database->getCollection("records\0x");
    }

    public function testDatabaseMagicAccessRefusesInvalidCollectionName(): void
    {
        $database = new Database(self::$manager, 'prod');

        $this->expectException(InvalidArgumentException::class);
        $database->{"records\0x"};
    }

    public function testClientMagicAccessRefusesInvalidDatabaseName(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->{'prod.audit'};
    }

    public function testInsertThroughHandleWithInvalidDatabaseNameIsRefused(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->getCollection('prod.audit', 'records')->insertOne(['marker' => 'writer']);
    }

    public function testInsertThroughHandleWithInvalidCollectionNameIsRefused(): void
    {
        $client = new Client(self::URI);

        $this->expectException(InvalidArgumentException::class);
        $client->getDatabase('prod')->getCollection("records\0x")->insertOne(['marker' => 'writer']);
    }

    public function testFileStorageBucketRefusesInvalidBucketName(): void
    {
        $this->expectException(InvalidArgumentException::class);
        new Bucket(self::$manager, 'prod', ['bucketName' => "records\0x"]);
    }
}
