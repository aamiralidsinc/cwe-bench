<?php

declare(strict_types=1);

namespace CweBench\MongoPhpLibrary\Security;

use MongoDB\ClientBulkWrite;
use MongoDB\Collection;
use MongoDB\Driver\Manager;
use MongoDB\Exception\InvalidArgumentException;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * A client bulk write targets a namespace; a namespace built from caller-supplied names
 * must address exactly those names.
 */
final class BulkWriteNamespaceSecurityTest extends TestCase
{
    private const URI = 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100';

    private static Manager $manager;

    public static function setUpBeforeClass(): void
    {
        self::$manager = new Manager(self::URI);
    }

    /** @return array<string, array{string, string}> */
    public static function provideInvalidNames(): array
    {
        return [
            'period in database name' => ['prod.audit', 'records'],
            'leading period in database name' => ['.prod', 'records'],
            'nul byte in database name' => ["prod\0audit", 'records'],
            'nul byte in collection name' => ['prod', "records\0x"],
        ];
    }

    #[DataProvider('provideInvalidNames')]
    public function testWithNamespaceRefusesInvalidNames(string $databaseName, string $collectionName): void
    {
        $bulkWrite = ClientBulkWrite::createWithCollection(new Collection(self::$manager, 'prod', 'records'));

        $this->expectException(InvalidArgumentException::class);
        $bulkWrite->withNamespace($databaseName, $collectionName);
    }

    public function testWithNamespaceRefusesInvalidNamesBeforeAnyWriteIsQueued(): void
    {
        $bulkWrite = ClientBulkWrite::createWithCollection(new Collection(self::$manager, 'prod', 'records'));

        try {
            $bulkWrite->withNamespace('prod.audit', 'records');
            self::fail('an invalid namespace was accepted');
        } catch (InvalidArgumentException) {
            // expected
        }

        /* The original bulk write must be unchanged and still able to queue a write for its
         * own, valid namespace. */
        $bulkWrite->insertOne(['marker' => 'writer']);
        self::assertSame(1, $bulkWrite->bulkWriteCommand->count());
    }
}
